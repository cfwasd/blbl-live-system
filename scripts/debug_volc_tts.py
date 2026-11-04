"""诊断火山豆包 TTS V3 接口原始响应结构（自动脱敏，不打印密钥与音频数据）。"""
import asyncio
import json
import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from admin.config import load_config

API_URL = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"


def mask(value, show=6):
    if not isinstance(value, str):
        return value
    if len(value) <= show:
        return "***"
    return value[:show] + "..." + f"(len={len(value)})"


async def main():
    cfg = load_config().volc_tts
    headers = {
        "X-Api-Key": cfg.api_key,
        "X-Api-Resource-Id": cfg.resource_id,
        "X-Api-Request-Id": str(uuid.uuid4()),
        "Content-Type": "application/json",
        "Connection": "keep-alive",
    }
    payload = {
        "req_params": {
            "text": "你好呀，这是语音测试",
            "speaker": cfg.speaker,
            "audio_params": {
                "format": "mp3",
                "sample_rate": 24000,
            },
        }
    }

    print(f"URL: {API_URL}")
    print(f"Resource-Id: {cfg.resource_id}")
    print(f"Speaker: {cfg.speaker}")
    print(f"Api-Key: {mask(cfg.api_key)}")
    print("-" * 60)

    async with httpx.AsyncClient(timeout=20.0) as client:
        async with client.stream("POST", API_URL, headers=headers, json=payload) as resp:
            print(f"HTTP 状态: {resp.status_code}")
            print(f"响应头 Content-Type: {resp.headers.get('content-type')}")
            print("-" * 60)
            lines_seen = 0
            async for line in resp.aiter_lines():
                if not line.strip():
                    continue
                lines_seen += 1
                if lines_seen > 12:
                    print("... (后续分块省略)")
                    break
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    print(f"[分块 {lines_seen}] 非 JSON 文本: {line[:200]}")
                    continue
                safe = {}
                for k, v in obj.items():
                    if k == "data":
                        safe[k] = mask(v) if v else v
                    elif k == "sentence":
                        safe[k] = f"<sentence对象 keys={list(v.keys()) if isinstance(v, dict) else type(v).__name__}>"
                    elif k == "usage":
                        safe[k] = v
                    else:
                        safe[k] = v
                print(f"[分块 {lines_seen}] {json.dumps(safe, ensure_ascii=False)}")

            if lines_seen == 0:
                print("！接口未返回任何分块内容")


if __name__ == "__main__":
    asyncio.run(main())
