import asyncio
import httpx
from typing import Callable, Optional
from admin.core.ingress.event import DanmuEvent

class BiliClientWrapper:
    def __init__(self, room_id: int, on_danmu: Callable[[DanmuEvent], asyncio.Future]):
        self.raw_room_id = room_id
        self.real_room_id = room_id
        self.on_danmu = on_danmu
        self.is_running = False

    async def resolve_real_room_id(self) -> int:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"https://api.live.bilibili.com/room/v1/Room/room_init?id={self.raw_room_id}")
                if res.status_code == 200:
                    data = res.json()
                    if data.get("code") == 0:
                        self.real_room_id = data["data"]["room_id"]
        except Exception:
            self.real_room_id = self.raw_room_id
        return self.real_room_id

    async def inject_mock_danmu(self, uname: str, content: str, price: float = 0.0, is_sc: bool = False):
        event = DanmuEvent(
            uid=123456,
            uname=uname,
            content=content,
            badge_name="粉丝团",
            badge_level=15,
            price=price,
            is_super_chat=is_sc
        )
        await self.on_danmu(event)
