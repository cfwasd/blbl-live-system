import os
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

    async def handle_incoming_danmu(event):
        # 1. 弹幕指令检查 (切歌/点歌等)
        cmd = parse_danmu_command(event.content)
        if cmd:
            if cmd.action in ("switch_song", "request_song"):
                await broadcaster.broadcast("bgm_action", {
                    "action": "switch",
                    "payload": cmd.payload
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
            return

        broadcaster.record_danmu(event.uname)

        # 3. 广播弹幕到大屏毛玻璃列表
        if event.is_super_chat:
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

        # 4. 触发 AI 思考与语音合成
        if p_res.can_trigger_ai:
            speech = await orchestrator.generate_response(event.uname, event.content)
            broadcaster.record_ai_reply(speech.tokens)
            await broadcaster.broadcast("ai_speech", {
                "id": speech.id,
                "text": speech.text,
                "audio": f"data:audio/mp3;base64,{speech.audio_base64}" if speech.audio_base64 else "",
                "motion": speech.motion,
                "expression": speech.expression
            })
            await broadcaster.broadcast("stats", broadcaster.get_current_stats())

    bili_client = BiliClientWrapper(config.bilibili.room_id, handle_incoming_danmu)

    # 挂载状态
    app.state.config = config
    app.state.broadcaster = broadcaster
    app.state.pipeline = pipeline
    app.state.orchestrator = orchestrator
    app.state.obs_client = obs_client
    app.state.bili_client = bili_client

    yield

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

# 挂载静态目录
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(os.path.join(static_dir, "admin"), exist_ok=True)
os.makedirs(os.path.join(static_dir, "live"), exist_ok=True)
app.mount("/admin", StaticFiles(directory=os.path.join(static_dir, "admin"), html=True), name="admin")
app.mount("/live", StaticFiles(directory=os.path.join(static_dir, "live"), html=True), name="live")
