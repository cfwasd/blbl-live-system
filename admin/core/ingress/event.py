import time
import uuid
from typing import Optional
from pydantic import BaseModel, Field

class DanmuEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    uid: int
    uname: str
    content: str
    badge_name: Optional[str] = ""
    badge_level: int = 0
    price: float = 0.0
    is_super_chat: bool = False
    timestamp: float = Field(default_factory=time.time)

class CommandAction(BaseModel):
    action: str  # switch_song, request_song, pause_music, resume_music, toggle_theme
    payload: str = ""
