import os
from typing import List, Optional
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from admin.config import AppConfig, save_config, get_config, VolcengineTTSConfig
from admin.core.tts.volcengine_client import VolcengineTTSClient

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

class TestTTSRequest(BaseModel):
    text: str
    api_key: Optional[str] = None
    resource_id: Optional[str] = None
    speaker: Optional[str] = None

@router.get("/api/config")
def get_current_config():
    return get_config()

@router.post("/api/config")
async def update_config(new_config: AppConfig, request: Request):
    save_config(new_config)
    # 同步刷新内存中的运行时配置，确保新保存的 Key/音色立即生效
    request.app.state.config = new_config
    orchestrator = request.app.state.orchestrator
    orchestrator.config = new_config
    orchestrator.llm.config = new_config.llm
    orchestrator.tts.config = new_config.volc_tts
    request.app.state.obs_client.config = new_config.obs

    broadcaster = request.app.state.broadcaster
    await broadcaster.log("INFO", "CONFIG", "后台配置已更新并持久化，AI 与语音客户端已热重载")
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

@router.post("/api/test/tts")
async def test_tts_endpoint(req: TestTTSRequest, request: Request):
    broadcaster = request.app.state.broadcaster
    config = request.app.state.config
    api_key = req.api_key or config.volc_tts.api_key
    resource_id = req.resource_id or config.volc_tts.resource_id
    speaker = req.speaker or config.volc_tts.speaker

    await broadcaster.log("INFO", "TTS", f"发起发音试听: '{req.text}' (音色: {speaker})")
    if not api_key:
        await broadcaster.log("WARN", "TTS", "未配置火山 API Key，无法合成试听音频")
        return {
            "status": "error",
            "message": "未配置火山 API Key！请先在【火山豆包语音】输入框中填入您的 X-Api-Key"
        }

    temp_cfg = VolcengineTTSConfig(
        api_key=api_key,
        resource_id=resource_id,
        speaker=speaker,
        format="mp3",
        sample_rate=24000
    )
    client = VolcengineTTSClient(temp_cfg)
    try:
        audio_b64 = await client.synthesize_base64_audio(req.text)
        if not audio_b64:
            await broadcaster.log("ERROR", "TTS", "火山接口未返回有效音频")
            return {
                "status": "error",
                "message": "火山语音接口未返回有效音频，请检查 X-Api-Key、Resource ID 或 Speaker 音色 ID 是否有效"
            }
        await broadcaster.log("INFO", "TTS", f"发音合成成功 (大小: {len(audio_b64)} 字节)")
        return {
            "status": "ok",
            "audio": f"data:audio/mp3;base64,{audio_b64}"
        }
    except Exception as e:
        await broadcaster.log("ERROR", "TTS", f"语音合成发生异常: {str(e)}")
        return {
            "status": "error",
            "message": f"请求火山接口发生异常: {str(e)}"
        }

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
