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
from admin.core.ai.worker import AIWorker
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
    ai_worker = AIWorker(orchestrator, broadcaster)
    ai_worker.start()
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

        # 4. 极速入队解耦的 AI 调度队列（<0.1ms 立即返回，WebSocket 长连接绝不阻塞）
        if p_res.can_trigger_ai:
            ai_worker.enqueue(event, score=p_res.score)

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
    app.state.ai_worker = ai_worker
    app.state.obs_client = obs_client
    app.state.bili_client = bili_client

    # 若配置了有效房间号，服务启动时自动开启 WebSocket 弹幕监听
    if config.bilibili.room_id:
        asyncio.create_task(bili_client.start(config.bilibili.room_id))

    await broadcaster.log("INFO", "SYSTEM", "虚拟AI主播管理服务已启动")

    yield

    await ai_worker.stop()
    await orchestrator.close()
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
