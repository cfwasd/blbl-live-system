import os
from typing import List, Optional
from pydantic import BaseModel, Field
import yaml

class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000

class BilibiliConfig(BaseModel):
    room_id: int = 21452505
    sessdata: str = ""

class LLMConfig(BaseModel):
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = "gemini-3.8-flash"
    system_prompt: str = (
        "你是雫酱（Shizuku），一位温柔治愈、偶尔有点害羞俏皮的深夜书房二次元虚拟主播。"
        "你在暖光书房里为观众开启深夜治愈电台。【互动规则】：1. 结合前序上下文自然接梗顺承话题；"
        "2. 可在句首使用情感标签如 [开心]、[害羞]、[思考]、[挥手] 驱动肢体动作，标签后为纯口语台词；"
        "3. 严禁圆括号心理描写如(笑)/(害羞)，严禁多余符号；4. 回复极度简炼（严格30字以内），富有温暖治愈感与情绪起伏，严禁冷漠客服腔。"
    )
    reasoning_effort: Optional[str] = "none"
    max_tokens: int = 60

class VolcengineTTSConfig(BaseModel):
    api_key: str = ""
    resource_id: str = "seed-tts-2.0"
    speaker: str = "zh_female_vv_uranus_bigtts"
    format: str = "mp3"
    sample_rate: int = 24000

class OBSConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 4455
    password: str = ""

class MascotConfig(BaseModel):
    scale: float = 1.0
    position_x: float = 0.8
    position_y: float = 0.9
    theme: str = "cozy_room"

class BGMItem(BaseModel):
    title: str
    file: str

class BGMConfig(BaseModel):
    default_volume: float = 0.35
    ducking_volume: float = 0.08
    playlist: List[BGMItem] = Field(default_factory=list)

class GuideItem(BaseModel):
    tag: str
    desc: str
    type: str = "normal"

class BroadcastNoticeConfig(BaseModel):
    marquee_text: str = "✨ 欢迎来到雫酱的深夜治愈书房！✦ 🎵 发送【点歌 歌名】可在线点播网易云流行与二次元歌曲 ✦ 🔀 发送【切歌】或【换首歌】可随时切换伴奏 ✦ 💬 弹幕畅聊，雫酱会语音与你温柔互动 ✦ 💎 投喂 SC 醒目留言享有专属发光置顶与优先语音答谢！"
    guide_items: List[GuideItem] = Field(default_factory=lambda: [
        GuideItem(tag="💬 弹幕聊天", desc="发送任意弹幕即刻触发 AI 思考与语音回答", type="chat"),
        GuideItem(tag="🎵 在线点歌", desc="发送【点歌 歌名】即播网易云高质音乐", type="music"),
        GuideItem(tag="🔀 快速切歌", desc="发送【切歌】或【下一首】切换在线伴奏", type="switch"),
        GuideItem(tag="💎 醒目留言", desc="投喂 SC 解锁专属置顶打赏卡与优先语音答谢", type="sc")
    ])

class AppConfig(BaseModel):
    server: ServerConfig = Field(default_factory=ServerConfig)
    bilibili: BilibiliConfig = Field(default_factory=BilibiliConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    volc_tts: VolcengineTTSConfig = Field(default_factory=VolcengineTTSConfig)
    obs: OBSConfig = Field(default_factory=OBSConfig)
    mascot: MascotConfig = Field(default_factory=MascotConfig)
    bgm: BGMConfig = Field(default_factory=BGMConfig)
    broadcast: BroadcastNoticeConfig = Field(default_factory=BroadcastNoticeConfig)

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "configs", "config.yaml")
_CURRENT_CONFIG: Optional[AppConfig] = None

def load_config(path: str = _CONFIG_PATH) -> AppConfig:
    global _CURRENT_CONFIG
    if not os.path.exists(path):
        _CURRENT_CONFIG = AppConfig()
        return _CURRENT_CONFIG
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    _CURRENT_CONFIG = AppConfig(**data)
    return _CURRENT_CONFIG

def get_config() -> AppConfig:
    global _CURRENT_CONFIG
    if _CURRENT_CONFIG is None:
        return load_config()
    return _CURRENT_CONFIG

def save_config(config: AppConfig, path: str = _CONFIG_PATH) -> None:
    global _CURRENT_CONFIG
    _CURRENT_CONFIG = config
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config.model_dump(), f, allow_unicode=True, sort_keys=False)
