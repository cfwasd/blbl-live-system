import os
import asyncio
import httpx
from typing import Tuple, Optional
from admin.config import LLMConfig

class LLMClient:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.total_tokens_used = 0
        self._client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        """获取或复用长连接 HTTP 客户端，避免每次请求重复进行 TCP 与 TLS 握手"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=8.0),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10, keepalive_expiry=60.0),
            )
        return self._client

    async def close(self):
        """释放底层 HTTP 连接池"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def complete(
        self,
        user_prompt: str = "",
        messages: Optional[list] = None
    ) -> Tuple[str, int]:
        # 自动化测试环境禁用真实外部调用，避免用例依赖外部网络与额度
        if os.environ.get("DISABLE_EXTERNAL_AI") == "1":
            return "（离线模拟）收到你的弹幕啦，Gemini娘在这里陪着你！", 25

        if not self.config.api_key:
            return f"（模拟回复）欢迎 {user_prompt} 呀，Gemini娘收到啦！", 25

        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        max_tokens = getattr(self.config, "max_tokens", 60) or 60

        # 支持多轮对话列表直接透传，缺省时自动拼接单轮问答
        if messages and isinstance(messages, list):
            req_messages = messages
        else:
            req_messages = [
                {"role": "system", "content": self.config.system_prompt},
                {"role": "user", "content": user_prompt}
            ]

        body = {
            "model": self.config.model,
            "messages": req_messages,
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        # 禁用或调低推理思考（Reasoning Effort），消除大模型数秒隐式思考延迟
        reasoning = getattr(self.config, "reasoning_effort", None)
        if reasoning:
            body["reasoning_effort"] = reasoning

        last_err: Optional[Exception] = None
        for attempt in range(2):
            try:
                client = await self.get_client()
                res = await client.post(url, headers=headers, json=body)
                res.raise_for_status()
                data = res.json()
                reply = data["choices"][0]["message"]["content"].strip()
                tokens = data.get("usage", {}).get("total_tokens", 30)
                self.total_tokens_used += tokens
                return reply, tokens
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as e:
                last_err = e
                # 异常时清理现有连接并重置客户端
                await self.close()
                if attempt == 0:
                    await asyncio.sleep(0.5)
        if last_err:
            raise last_err
        return "", 0
