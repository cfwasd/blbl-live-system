import os
from typing import List
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from admin.config import AppConfig, save_config, get_config

router = APIRouter()

class SpeakRequest(BaseModel):
    text: str

class DanmuTestRequest(BaseModel):
    uname: str = "测试观众"
    content: str = "主播好呀"
    price: float = 0.0
    is_sc: bool = False

class BannedWordsRequest(BaseModel):
    words: List[str]

@router.get("/api/config")
def get_current_config():
    return get_config()

@router.post("/api/config")
async def update_config(new_config: AppConfig, request: Request):
    save_config(new_config)
    # 触发配置热同步广播到直播大屏
    broadcaster = request.app.state.broadcaster
    await broadcaster.broadcast("config_sync", {
        "theme": new_config.mascot.theme,
        "mascot": {
            "scale": new_config.mascot.scale,
            "x": new_config.mascot.position_x,
            "y": new_config.mascot.position_y
        },
        "bgm": {
            "volume": new_config.bgm.default_volume
        }
    })
    return {"status": "ok"}

@router.post("/api/broadcast/speak")
async def manual_speak(req: SpeakRequest, request: Request):
    orchestrator = request.app.state.orchestrator
    broadcaster = request.app.state.broadcaster
    audio_b64 = await orchestrator.tts.synthesize_base64_audio(req.text)
    payload = {
        "id": "manual",
        "text": req.text,
        "audio": f"data:audio/mp3;base64,{audio_b64}" if audio_b64 else "",
        "motion": "Wave",
        "expression": "smile"
    }
    await broadcaster.broadcast("ai_speech", payload)
    return {"status": "ok"}

@router.post("/api/test/danmu")
async def inject_danmu(req: DanmuTestRequest, request: Request):
    bili_client = request.app.state.bili_client
    await bili_client.inject_mock_danmu(req.uname, req.content, req.price, req.is_sc)
    return {"status": "ok"}

@router.get("/api/banned-words")
def get_banned_words(request: Request):
    pipeline = request.app.state.pipeline
    return {"words": pipeline.filter.words}

@router.post("/api/banned-words")
def update_banned_words(req: BannedWordsRequest, request: Request):
    pipeline = request.app.state.pipeline
    pipeline.filter.update_words(req.words)
    return {"status": "ok", "count": len(pipeline.filter.words)}

@router.post("/api/live/start")
def live_start(request: Request):
    obs = request.app.state.obs_client
    success = obs.start_streaming()
    return {"status": "ok" if success else "failed"}

@router.post("/api/live/stop")
def live_stop(request: Request):
    obs = request.app.state.obs_client
    success = obs.stop_streaming()
    return {"status": "ok" if success else "failed"}

@router.get("/api/live/status")
def live_status(request: Request):
    obs = request.app.state.obs_client
    return obs.get_status()
