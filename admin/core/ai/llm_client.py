import httpx
from typing import Tuple, Optional
from admin.config import LLMConfig

class LLMClient:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.total_tokens_used = 0

    async def complete(self, user_prompt: str) -> Tuple[str, int]:
        if not self.config.api_key:
            return f"（模拟回复）欢迎 {user_prompt} 呀，Gemini娘收到啦！", 25

        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        body = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": self.config.system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 100,
            "temperature": 0.7
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(url, headers=headers, json=body)
            res.raise_for_status()
            data = res.json()
            reply = data["choices"][0]["message"]["content"].strip()
            tokens = data.get("usage", {}).get("total_tokens", 30)
            self.total_tokens_used += tokens
            return reply, tokens
