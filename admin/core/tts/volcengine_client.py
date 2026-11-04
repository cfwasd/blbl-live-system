import uuid
import json
import httpx
from typing import Optional
from admin.config import VolcengineTTSConfig

class VolcengineTTSClient:
    API_URL = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"

    def __init__(self, config: VolcengineTTSConfig):
        self.config = config

    def build_headers(self) -> dict:
        return {
            "X-Api-Key": self.config.api_key,
            "X-Api-Resource-Id": self.config.resource_id,
            "X-Api-Request-Id": str(uuid.uuid4()),
            "Content-Type": "application/json",
            "Connection": "keep-alive"
        }

    def build_payload(self, text: str) -> dict:
        return {
            "req_params": {
                "text": text,
                "speaker": self.config.speaker,
                "model": "seed-tts-2.0-standard",
                "audio_params": {
                    "format": self.config.format,
                    "sample_rate": self.config.sample_rate
                }
            }
        }

    async def synthesize_base64_audio(self, text: str) -> str:
        """调用火山 V3 HTTP 单向流式接口，聚合分块返回完整的 Base64 音频"""
        if not self.config.api_key:
            return ""  # 未配 Key 时返回空以触发静默降级

        headers = self.build_headers()
        payload = self.build_payload(text)

        chunks = []
        async with httpx.AsyncClient(timeout=15.0) as client:
            async with client.stream("POST", self.API_URL, headers=headers, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk_json = json.loads(line)
                        if chunk_json.get("code") == 0 and "data" in chunk_json:
                            chunks.append(chunk_json["data"])
                    except json.JSONDecodeError:
                        continue
        return "".join(chunks)
