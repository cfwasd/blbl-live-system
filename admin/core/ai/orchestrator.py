import re
from collections import deque
from typing import Optional, List, Dict, Tuple
from pydantic import BaseModel
from admin.config import AppConfig
from admin.core.ai.llm_client import LLMClient
from admin.core.tts.volcengine_client import VolcengineTTSClient

class AISpeechPackage(BaseModel):
    id: str
    text: str
    audio_base64: str = ""
    motion: str = "Wave"
    expression: str = "smile"
    tokens: int = 0

_RE_EMOTION_TAG = re.compile(r"^\[([a-zA-Z一-龥]+)\]\s*")

EMOTION_MAP = {
    "开心": ("Happy", "smile"),
    "笑": ("Happy", "smile"),
    "happy": ("Happy", "smile"),
    "smile": ("Happy", "smile"),
    "害羞": ("Shy", "blush"),
    "傲娇": ("Shy", "blush"),
    "脸红": ("Shy", "blush"),
    "shy": ("Shy", "blush"),
    "blush": ("Shy", "blush"),
    "思考": ("Think", "think"),
    "疑惑": ("Think", "think"),
    "好奇": ("Think", "think"),
    "think": ("Think", "think"),
    "挥手": ("Wave", "smile"),
    "招呼": ("Wave", "smile"),
    "欢迎": ("Wave", "smile"),
    "wave": ("Wave", "smile"),
}

def extract_emotion(text: str) -> Tuple[str, str, str]:
    """
    从大模型回复中提取情感标签与纯净台词
    返回: (clean_text, motion, expression)
    """
    motion = "Wave"
    expression = "smile"
    clean_text = text.strip()

    # 1. 尝试显式标签提取 [害羞] / [开心] 等
    match = _RE_EMOTION_TAG.match(clean_text)
    if match:
        tag = match.group(1).lower()
        clean_text = clean_text[match.end():].strip()
        if tag in EMOTION_MAP:
            motion, expression = EMOTION_MAP[tag]
    else:
        # 2. 隐式关键词匹配
        if any(k in clean_text for k in ("哈哈", "好耶", "开心", "嘻嘻", "喜欢", "太棒了")):
            motion, expression = ("Happy", "smile")
        elif any(k in clean_text for k in ("害羞", "讨厌", "哼", "笨蛋", "才没有", "才不")):
            motion, expression = ("Shy", "blush")
        elif any(k in clean_text for k in ("？", "?", "为什么", "好奇", "想一想", "唔")):
            motion, expression = ("Think", "think")
        elif any(k in clean_text for k in ("欢迎", "晚上好", "你好", "嗨", "拜拜")):
            motion, expression = ("Wave", "smile")

    return clean_text or text, motion, expression

class AIOrchestrator:
    def __init__(self, config: AppConfig, max_history_turns: int = 4):
        self.config = config
        self.llm = LLMClient(config.llm)
        self.tts = VolcengineTTSClient(config.volc_tts)
        self.max_history_turns = max_history_turns
        # 维护直播间全局滑动对话历史：保存最近 N 轮 {uname, question, reply}
        self.dialogue_history: deque = deque(maxlen=max_history_turns)

    def build_messages(self, uname: str, content: str) -> List[Dict[str, str]]:
        """组装带有多轮上下文的 Prompt 列表，使大模型自然感知前序观众聊了什么"""
        messages = [
            {"role": "system", "content": self.config.llm.system_prompt}
        ]
        for turn in self.dialogue_history:
            messages.append({"role": "user", "content": f"观众【{turn['uname']}】说：{turn['question']}"})
            messages.append({"role": "assistant", "content": turn["reply"]})

        messages.append({"role": "user", "content": f"观众【{uname}】说：{content}"})
        return messages

    def clear_history(self):
        """清空对话历史（转场、重置话题时使用）"""
        self.dialogue_history.clear()

    async def generate_response(self, uname: str, content: str) -> AISpeechPackage:
        messages = self.build_messages(uname, content)
        reply_text, tokens = await self.llm.complete(
            user_prompt=f"观众【{uname}】说：{content}",
            messages=messages
        )
        # 归一化：折叠换行与多余空白，避免大屏气泡与 TTS 出现断行杂质
        reply_text = " ".join(reply_text.split())

        # 提取情感与动作意图，清洗掉括号标签以防 TTS 念出 "[开心]"
        clean_text, motion, expression = extract_emotion(reply_text)

        # 将有效回复压入历史滑窗，供下一轮弹幕连贯互动
        if clean_text:
            self.dialogue_history.append({
                "uname": uname,
                "question": content,
                "reply": clean_text
            })

        audio_b64 = await self.tts.synthesize_base64_audio(clean_text)

        return AISpeechPackage(
            id=f"speech_{tokens}",
            text=clean_text,
            audio_base64=audio_b64,
            motion=motion,
            expression=expression,
            tokens=tokens
        )

    async def close(self):
        await self.llm.close()
        await self.tts.close()
