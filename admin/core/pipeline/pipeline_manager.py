import re
from typing import Optional
from pydantic import BaseModel
from admin.core.ingress.event import DanmuEvent
from admin.core.pipeline.aho_corasick import SensitiveWordFilter
from admin.core.pipeline.cooldown import UIDCooldownManager

class PipelineResult(BaseModel):
    event: DanmuEvent
    is_blocked: bool = False
    reason: str = ""
    score: int = 10
    can_trigger_ai: bool = False

class PipelineManager:
    def __init__(self, banned_words_path: str, cooldown_seconds: float = 10.0):
        self.filter = SensitiveWordFilter(banned_words_path)
        self.cooldown = UIDCooldownManager(cooldown_seconds)

    def process(self, event: DanmuEvent) -> PipelineResult:
        # 1. 文本规范化与长度截断
        cleaned = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", event.content).strip()
        if len(cleaned) > 50:
            cleaned = cleaned[:50]
        event.content = cleaned

        # 2. 敏感词匹配
        matched = self.filter.contains_sensitive(event.content)
        if matched:
            return PipelineResult(event=event, is_blocked=True, reason="sensitive_word")

        # 3. 动态打分
        score = 10
        if event.badge_level >= 10:
            score = 30
        if event.is_super_chat or event.price > 0:
            score = 100

        # 4. UID 冷却检查
        can_trigger = False
        if score == 100:
            can_trigger = True  # 大额 SC/礼物穿透冷却
        else:
            can_trigger = self.cooldown.check_and_update(event.uid)

        return PipelineResult(event=event, is_blocked=False, score=score, can_trigger_ai=can_trigger)
