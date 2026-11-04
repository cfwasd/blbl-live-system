import asyncio
import httpx
from typing import Callable, Optional, Dict, Any
import blivedm
from admin.core.ingress.event import DanmuEvent

class BiliHandler(blivedm.BaseHandler):
    def __init__(self, callback: Callable[[DanmuEvent], Any], log_cb: Optional[Callable[[str, str, str], Any]] = None):
        super().__init__()
        self.callback = callback
        self.log_cb = log_cb

    def _on_danmaku(self, client: blivedm.BLiveClient, message: blivedm.DanmakuMessage):
        event = DanmuEvent(
            uid=message.uid,
            uname=message.uname,
            content=message.msg,
            badge_name=message.medal_name or "",
            badge_level=message.medal_level or 0,
            price=0.0,
            is_super_chat=False
        )
        if self.log_cb:
            asyncio.create_task(self.log_cb("INFO", "DANMU", f"[{message.uname}] {message.msg}"))
        asyncio.create_task(self.callback(event))

    def _on_super_chat(self, client: blivedm.BLiveClient, message: blivedm.SuperChatMessage):
        event = DanmuEvent(
            uid=message.uid,
            uname=message.uname,
            content=message.message,
            price=float(message.price),
            is_super_chat=True
        )
        if self.log_cb:
            asyncio.create_task(self.log_cb("WARN", "SUPERCHAT", f"￥{message.price} [{message.uname}] {message.message}"))
        asyncio.create_task(self.callback(event))

    def _on_gift(self, client: blivedm.BLiveClient, message: blivedm.GiftMessage):
        if message.coin_type == "gold" and message.total_coin > 0:
            price = message.total_coin / 1000.0
            event = DanmuEvent(
                uid=message.uid,
                uname=message.uname,
                content=f"送出礼物【{message.gift_name}】x{message.num}",
                price=price,
                is_super_chat=False
            )
            if self.log_cb:
                asyncio.create_task(self.log_cb("INFO", "GIFT", f"[{message.uname}] 赠送 {message.gift_name} x{message.num} (￥{price:.1f})"))
            asyncio.create_task(self.callback(event))

class BiliClientWrapper:
    def __init__(self, room_id: int, on_danmu: Callable[[DanmuEvent], Any], log_cb: Optional[Callable[[str, str, str], Any]] = None):
        self.raw_room_id = room_id
        self.real_room_id = room_id
        self.on_danmu = on_danmu
        self.log_cb = log_cb
        self.bili_client: Optional[blivedm.BLiveClient] = None
        self.is_running = False
        self.room_info: Dict[str, Any] = {}
        self._task: Optional[asyncio.Task] = None

    async def resolve_real_room_id(self, target_id: Optional[int] = None) -> int:
        query_id = target_id or self.raw_room_id
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"https://api.live.bilibili.com/room/v1/Room/room_init?id={query_id}")
                if res.status_code == 200:
                    data = res.json()
                    if data.get("code") == 0:
                        real_id = data["data"]["room_id"]
                        if not target_id:
                            self.real_room_id = real_id
                        return real_id
        except Exception as e:
            if self.log_cb:
                asyncio.create_task(self.log_cb("WARN", "BILI", f"换算房间号失败: {e}"))
        return query_id

    async def fetch_room_details(self, target_id: Optional[int] = None) -> Dict[str, Any]:
        real_id = await self.resolve_real_room_id(target_id)
        info = {
            "room_id": real_id,
            "raw_id": target_id or self.raw_room_id,
            "title": "未知直播间",
            "uname": "未知主播",
            "live_status": 0,
            "area_name": "未知",
            "online": 0,
            "cover": ""
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"https://api.live.bilibili.com/room/v1/Room/get_info?room_id={real_id}")
                if res.status_code == 200:
                    data = res.json()
                    if data.get("code") == 0:
                        d = data["data"]
                        info["title"] = d.get("title", "")
                        info["live_status"] = d.get("live_status", 0)
                        info["area_name"] = d.get("area_name", "")
                        info["online"] = d.get("online", 0)
                        info["cover"] = d.get("user_cover", "")

                # 获取主播昵称
                u_res = await client.get(f"https://api.live.bilibili.com/live_user/v1/UserInfo/get_anchor_in_room?roomid={real_id}")
                if u_res.status_code == 200:
                    u_data = u_res.json()
                    if u_data.get("code") == 0:
                        info["uname"] = u_data["data"]["info"].get("uname", "")
        except Exception as e:
            if self.log_cb:
                asyncio.create_task(self.log_cb("WARN", "BILI", f"获取房间信息异常: {e}"))

        self.room_info = info
        return info

    async def start(self, target_id: Optional[int] = None) -> bool:
        if self.is_running:
            await self.stop()

        if target_id:
            self.raw_room_id = target_id

        self.real_room_id = await self.resolve_real_room_id(self.raw_room_id)
        await self.fetch_room_details(self.real_room_id)

        try:
            self.bili_client = blivedm.BLiveClient(self.real_room_id, ssl=True)
            handler = BiliHandler(self.on_danmu, self.log_cb)
            self.bili_client.add_handler(handler)
            self.bili_client.start()
            self.is_running = True
            if self.log_cb:
                await self.log_cb("INFO", "BILI", f"已连接 B站 WebSocket 直播间 [{self.real_room_id}] (主播: {self.room_info.get('uname', '未知')})")
            return True
        except Exception as e:
            self.is_running = False
            if self.log_cb:
                await self.log_cb("ERROR", "BILI", f"连接直播间失败: {e}")
            return False

    async def stop(self) -> bool:
        if self.bili_client:
            try:
                await self.bili_client.stop_and_close()
            except Exception:
                pass
            self.bili_client = None
        self.is_running = False
        if self.log_cb:
            await self.log_cb("INFO", "BILI", f"已断开 B站 WebSocket 直播间 [{self.real_room_id}]")
        return True

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_running": self.is_running,
            "raw_room_id": self.raw_room_id,
            "real_room_id": self.real_room_id,
            "room_info": self.room_info
        }

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
        if self.log_cb:
            tag = "MOCK_SC" if is_sc else "MOCK_DANMU"
            await self.log_cb("INFO", tag, f"[{uname}] {content}")
        await self.on_danmu(event)
