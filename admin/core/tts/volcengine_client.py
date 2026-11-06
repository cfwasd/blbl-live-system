import os
import uuid
import json
import httpx
from typing import Optional
from admin.config import VolcengineTTSConfig

class VolcengineTTSClient:
    API_URL = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"

    def __init__(self, config: VolcengineTTSConfig):
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        """复用长连接 HTTP 客户端，消除火山语音合成每次建立 TLS/TCP 的网络开销"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(20.0, connect=5.0),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10, keepalive_expiry=60.0),
            )
        return self._client

    async def close(self):
        """释放底层 HTTP 连接池"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

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
        # 自动化测试环境禁用真实外部调用
        if os.environ.get("DISABLE_EXTERNAL_AI") == "1":
            return ""
        if not self.config.api_key:
            return ""  # 未配 Key 时返回空以触发静默降级

        headers = self.build_headers()
        payload = self.build_payload(text)

        chunks = []
        raw_lines = 0
        first_line_preview = ""
        client = await self.get_client()
        try:
            async with client.stream("POST", self.API_URL, headers=headers, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or not line.strip():
                        continue
                    raw_lines += 1
                    stripped = line.strip()
                    if raw_lines == 1:
                        first_line_preview = stripped[:300]
                    if stripped.startswith("data:"):
                        stripped = stripped[5:].strip()
                    try:
                        chunk_json = json.loads(stripped)
                        if chunk_json.get("code") == 0:
                            chunk_data = chunk_json.get("data")
                            if chunk_data and isinstance(chunk_data, str):
                                chunks.append(chunk_data)
                    except (json.JSONDecodeError, AttributeError):
                        continue
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError):
            await self.close()
            # 网络闪断时尝试重连一次
            try:
                retry_client = await self.get_client()
                async with retry_client.stream("POST", self.API_URL, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line or not line.strip():
                            continue
                        stripped = line.strip()
                        if stripped.startswith("data:"):
                            stripped = stripped[5:].strip()
                        try:
                            chunk_json = json.loads(stripped)
                            if chunk_json.get("code") == 0 and chunk_json.get("data"):
                                chunks.append(chunk_json["data"])
                        except Exception:
                            continue
            except Exception:
                pass
        if not chunks:
            print(f"[VolcTTS] 未收集到音频分块 (行数={raw_lines}, 首行={first_line_preview})", flush=True)
        return "".join(chunks)
