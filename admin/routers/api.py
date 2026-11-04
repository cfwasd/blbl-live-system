import os
from typing import List, Optional
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

class BiliConnectRequest(BaseModel):
    room_id: Optional[int] = None

@router.get("/api/config")
def get_current_config():
    return get_config()

@router.post("/api/config")
async def update_config(new_config: AppConfig, request: Request):
    save_config(new_config)
    broadcaster = request.app.state.broadcaster
    await broadcaster.log("INFO", "CONFIG", "后台配置已更新并持久化至 config.yaml")
    # 触发配置热同步广播到直播大屏
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

@router.get("/api/logs")
def get_logs(request: Request):
    broadcaster = request.app.state.broadcaster
    return {"logs": broadcaster.get_recent_logs()}

@router.get("/api/bili/status")
def get_bili_status(request: Request):
    bili = request.app.state.bili_client
    return bili.get_status()

@router.post("/api/bili/test")
async def test_bili_room(req: BiliConnectRequest, request: Request):
    bili = request.app.state.bili_client
    target_id = req.room_id or bili.raw_room_id
    info = await bili.fetch_room_details(target_id)
    return {"status": "ok", "info": info}

@router.post("/api/bili/connect")
async def connect_bili_room(req: BiliConnectRequest, request: Request):
    bili = request.app.state.bili_client
    target_id = req.room_id or bili.raw_room_id
    success = await bili.start(target_id)
    return {"status": "ok" if success else "failed", "details": bili.get_status()}

@router.post("/api/bili/disconnect")
async def disconnect_bili_room(request: Request):
    bili = request.app.state.bili_client
    await bili.stop()
    return {"status": "ok"}

@router.post("/api/broadcast/speak")
async def manual_speak(req: SpeakRequest, request: Request):
    orchestrator = request.app.state.orchestrator
    broadcaster = request.app.state.broadcaster
    await broadcaster.log("INFO", "SPEAK", f"房管发起插播: {req.text}")
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
async def update_banned_words(req: BannedWordsRequest, request: Request):
    pipeline = request.app.state.pipeline
    pipeline.filter.update_words(req.words)
    broadcaster = request.app.state.broadcaster
    await broadcaster.log("INFO", "CONFIG", f"敏感词库已更新，词条数: {len(pipeline.filter.words)}")
    return {"status": "ok", "count": len(pipeline.filter.words)}

@router.post("/api/live/start")
async def live_start(request: Request):
    obs = request.app.state.obs_client
    success = obs.start_streaming()
    broadcaster = request.app.state.broadcaster
    await broadcaster.log("INFO", "OBS", f"发送开播指令，结果: {'成功' if success else '失败'}")
    return {"status": "ok" if success else "failed"}

@router.post("/api/live/stop")
async def live_stop(request: Request):
    obs = request.app.state.obs_client
    success = obs.stop_streaming()
    broadcaster = request.app.state.broadcaster
    await broadcaster.log("INFO", "OBS", f"发送下播指令，结果: {'成功' if success else '失败'}")
    return {"status": "ok" if success else "failed"}

@router.get("/api/live/status")
def live_status(request: Request):
    obs = request.app.state.obs_client
    return obs.get_status()
