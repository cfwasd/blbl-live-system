"""复现 /api/test/tts 端点的内部调用路径，定位返回空音频的原因。"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from admin.config import load_config, VolcengineTTSConfig
from admin.core.tts.volcengine_client import VolcengineTTSClient


async def main():
    config = load_config()
    temp_cfg = VolcengineTTSConfig(
        api_key=config.volc_tts.api_key,
        resource_id=config.volc_tts.resource_id,
        speaker=config.volc_tts.speaker,
        format="mp3",
        sample_rate=24000,
    )
    client = VolcengineTTSClient(temp_cfg)
    print("headers keys:", sorted(client.build_headers().keys()))
    audio = await client.synthesize_base64_audio("你好呀，这是语音测试")
    print("audio len:", len(audio))


if __name__ == "__main__":
    asyncio.run(main())
