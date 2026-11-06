import os
import time
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from admin.config import load_config
from admin.core.broadcast.broadcaster import Broadcaster
from admin.core.pipeline.pipeline_manager import PipelineManager
from admin.core.ingress.command_parser import parse_danmu_command
from admin.core.ingress.bili_client import BiliClientWrapper
from admin.core.ai.orchestrator import AIOrchestrator
from admin.core.obs.obs_client import OBSClientWrapper
from admin.core.music.netease import search_netease_song
from admin.routers import api, stream

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动初始化
    config = load_config()
    broadcaster = Broadcaster()
    banned_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "configs", "banned_words.txt")
    pipeline = PipelineManager(banned_path)
    orchestrator = AIOrchestrator(config)
    obs_client = OBSClientWrapper(config.obs)
    seen_users = set()

    async def handle_incoming_danmu(event):
        # 新观众入场迎宾检测
        if event.uname and event.uname not in seen_users:
            seen_users.add(event.uname)
            await broadcaster.broadcast("viewer_welcome", {
                "uname": event.uname,
                "badge": event.badge_name or "粉丝团",
                "level": event.badge_level or 1,
                "time": time.strftime("%H:%M:%S")
            })

        # 1. 弹幕指令检查 (切歌/点歌等)
        cmd = parse_danmu_command(event.content)
        if cmd:
            await broadcaster.log("INFO", "CMD", f"观众【{event.uname}】触发指令: {cmd.action} {cmd.payload}")
            if cmd.action == "request_song":
                async def _do_online_request(query: str, uname: str):
                    song = await search_netease_song(query)
                    if song:
                        await broadcaster.log("INFO", "BGM", f"观众【{uname}】在线点歌成功: 《{song['title']}》- {song['artist']}")
                        await broadcaster.broadcast("bgm_action", {
                            "action": "play_song",
                            "song": song,
                            "uname": uname
                        })
                    else:
                        await broadcaster.log("WARN", "BGM", f"未找到观众【{uname}】点播的歌曲: {query}")
                        await broadcaster.broadcast("bgm_action", {
                            "action": "switch",
                            "payload": query,
                            "uname": uname
                        })
                asyncio.create_task(_do_online_request(cmd.payload, event.uname))
            elif cmd.action == "switch_song":
                await broadcaster.broadcast("bgm_action", {
                    "action": "switch",
                    "payload": cmd.payload,
                    "uname": event.uname
                })
            elif cmd.action in ("pause_music", "resume_music"):
                await broadcaster.broadcast("bgm_action", {
                    "action": "pause" if cmd.action == "pause_music" else "play"
                })
            elif cmd.action == "toggle_theme":
                await broadcaster.broadcast("config_sync", {"theme": "toggle"})
            return

        # 2. 走风控过滤与打分管线
        p_res = pipeline.process(event)
        if p_res.is_blocked:
            broadcaster.record_blocked()
            await broadcaster.log("WARN", "BLOCK", f"敏感词拦截: [{event.uname}] {event.content}")
            return

        broadcaster.record_danmu(event.uname)

        # 3. 广播弹幕到大屏毛玻璃列表
        if event.is_super_chat:
            await broadcaster.log("WARN", "SC", f"收到醒目留言 ￥{event.price} [{event.uname}]: {event.content}")
            await broadcaster.broadcast("super_chat", {
                "id": event.id,
                "uname": event.uname,
                "price": event.price,
                "content": event.content,
                "duration": 60
            })
        else:
            await broadcaster.broadcast("danmu", {
                "id": event.id,
                "uname": event.uname,
                "content": event.content,
                "badge": event.badge_name,
                "level": event.badge_level
            })

        # 定期同步实时统计数据
        await broadcaster.broadcast("stats", broadcaster.get_current_stats())

        # 4. 触发 AI 思考与语音合成（任何外部依赖异常都不得中断主循环）
        if p_res.can_trigger_ai:
            await broadcaster.log("INFO", "AI", f"正在为观众【{event.uname}】的弹幕生成回复...")
            # 立即向大屏广播正在思考事件，大屏立刻浮现提问卡片与思考动效，零延迟反馈
            await broadcaster.broadcast("ai_thinking", {
                "uname": event.uname,
                "question": event.content,
                "badge": event.badge_name,
                "level": event.badge_level,
                "is_super_chat": event.is_super_chat,
                "price": event.price
            })
            try:
                speech = await orchestrator.generate_response(event.uname, event.content)
            except Exception as e:
                await broadcaster.log("ERROR", "AI", f"AI 回复生成失败: {type(e).__name__}: {e}")
                speech = None
            if speech:
                broadcaster.record_ai_reply(speech.tokens)
                await broadcaster.log("INFO", "AI", f"回复台词: {speech.text} (消耗 Token: {speech.tokens})")

                if speech.audio_base64:
                    await broadcaster.log("INFO", "TTS", "火山豆包语音合成完成，下发音频流")
                else:
                    await broadcaster.log("WARN", "TTS", "未获得音频流，本次仅下发字幕（请检查火山语音配置）")

                await broadcaster.broadcast("ai_speech", {
                    "id": speech.id,
                    "text": speech.text,
                    "audio": f"data:audio/mp3;base64,{speech.audio_base64}" if speech.audio_base64 else "",
                    "motion": speech.motion,
                    "expression": speech.expression,
                    "reply_to": {
                        "uname": event.uname,
                        "question": event.content,
                        "badge": event.badge_name,
                        "level": event.badge_level,
                        "is_super_chat": event.is_super_chat,
                        "price": event.price
                    }
                })
                await broadcaster.broadcast("stats", broadcaster.get_current_stats())

    bili_client = BiliClientWrapper(
        config.bilibili.room_id,
        handle_incoming_danmu,
        broadcaster.log,
        sessdata=config.bilibili.sessdata,
    )

    # 挂载状态
    app.state.config = config
    app.state.broadcaster = broadcaster
    app.state.pipeline = pipeline
    app.state.orchestrator = orchestrator
    app.state.obs_client = obs_client
    app.state.bili_client = bili_client

    # 若配置了有效房间号，服务启动时自动开启 WebSocket 弹幕监听
    if config.bilibili.room_id:
        asyncio.create_task(bili_client.start())

    await broadcaster.log("INFO", "SYSTEM", "虚拟AI主播管理服务已启动")

    yield

    if bili_client.is_running:
        await bili_client.stop()

app = FastAPI(title="Virtual AI Live System", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router)
app.include_router(stream.router)

# 挂载静态目录与外部模型目录
static_dir = os.path.join(os.path.dirname(__file__), "static")
models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
os.makedirs(os.path.join(static_dir, "admin"), exist_ok=True)
os.makedirs(os.path.join(static_dir, "live"), exist_ok=True)
os.makedirs(models_dir, exist_ok=True)
app.mount("/admin", StaticFiles(directory=os.path.join(static_dir, "admin"), html=True), name="admin")
app.mount("/live", StaticFiles(directory=os.path.join(static_dir, "live"), html=True), name="live")
app.mount("/models", StaticFiles(directory=models_dir), name="models")
