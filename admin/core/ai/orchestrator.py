from collections import deque
from typing import Optional, List, Dict
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

        # 将有效回复压入历史滑窗，供下一轮弹幕连贯互动
        if reply_text:
            self.dialogue_history.append({
                "uname": uname,
                "question": content,
                "reply": reply_text
            })

        audio_b64 = await self.tts.synthesize_base64_audio(reply_text)

        return AISpeechPackage(
            id=f"speech_{tokens}",
            text=reply_text,
            audio_base64=audio_b64,
            motion="Wave",
            expression="smile",
            tokens=tokens
        )

    async def close(self):
        await self.llm.close()
        await self.tts.close()
