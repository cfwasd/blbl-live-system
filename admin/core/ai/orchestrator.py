from pydantic import BaseModel
from typing import Optional
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
    def __init__(self, config: AppConfig):
        self.config = config
        self.llm = LLMClient(config.llm)
        self.tts = VolcengineTTSClient(config.volc_tts)

    async def generate_response(self, uname: str, content: str) -> AISpeechPackage:
        prompt = f"观众【{uname}】说：{content}"
        reply_text, tokens = await self.llm.complete(prompt)
        audio_b64 = await self.tts.synthesize_base64_audio(reply_text)

        return AISpeechPackage(
            id=f"speech_{tokens}",
            text=reply_text,
            audio_base64=audio_b64,
            motion="Wave",
            expression="smile",
            tokens=tokens
        )
