import asyncio
import hashlib
import json
import logging
import time
import urllib.parse
import zlib
from typing import Callable, Optional, Dict, Any

import aiohttp
import blivedm
import brotli
import httpx
from admin.core.ingress.event import DanmuEvent

logging.getLogger("blivedm").setLevel(logging.ERROR)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "https://live.bilibili.com/",
    "Origin": "https://live.bilibili.com",
}

MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52,
]


def _sign_wbi(params: Dict[str, Any], mixin_key: str) -> Dict[str, Any]:
    signed = dict(params)
    signed["wts"] = int(time.time())
    signed = dict(sorted(signed.items()))
    signed = {
        k: "".join(c for c in str(v) if c not in "!'()*")
        for k, v in signed.items()
    }
    query = urllib.parse.urlencode(signed)
    signed["w_rid"] = hashlib.md5((query + mixin_key).encode("utf-8")).hexdigest()
    return signed


class WbiBLiveClient(blivedm.BLiveClient):
    """兼容 B 站最新 WBI 签名、buvid3 校验与 zlib/brotli 解包的弹幕 WebSocket 客户端。"""

    def __init__(
        self,
        room_id: int,
        sessdata: str = "",
        log_cb: Optional[Callable[[str, str, str], Any]] = None,
        ssl: bool = True,
    ):
        session = aiohttp.ClientSession(
            headers=DEFAULT_HEADERS,
            timeout=aiohttp.ClientTimeout(total=15),
        )
        super().__init__(room_id, uid=0, session=session, heartbeat_interval=30, ssl=ssl)
        self._own_session = True
        self._sessdata = sessdata.strip()
        self._buvid3 = ""
        self._mixin_key = ""
        self._log_cb = log_cb

    async def _emit_log(self, level: str, tag: str, msg: str):
        if self._log_cb:
            try:
                await self._log_cb(level, tag, msg)
            except Exception:
                pass

    async def _fetch_wbi_and_buvid(self, client: httpx.AsyncClient):
        try:
            spi_res = await client.get("https://api.bilibili.com/x/frontend/finger/spi")
            if spi_res.status_code == 200:
                spi_data = spi_res.json()
                if spi_data.get("code") == 0:
                    self._buvid3 = spi_data["data"].get("b_3", "")
                    if self._buvid3:
                        client.cookies.set("buvid3", self._buvid3)
        except Exception:
            pass

        if self._sessdata:
            client.cookies.set("SESSDATA", self._sessdata)

        try:
            nav_res = await client.get("https://api.bilibili.com/x/web-interface/nav")
            if nav_res.status_code == 200:
                nav_data = nav_res.json()
                data_obj = nav_data.get("data") or {}
                if data_obj.get("mid"):
                    self._uid = int(data_obj["mid"])
                wbi_img = data_obj.get("wbi_img") or {}
                img_url = wbi_img.get("img_url", "")
                sub_url = wbi_img.get("sub_url", "")
                if img_url and sub_url:
                    img_key = img_url.rsplit("/", 1)[1].split(".")[0]
                    sub_key = sub_url.rsplit("/", 1)[1].split(".")[0]
                    raw = img_key + sub_key
                    self._mixin_key = "".join(raw[i] for i in MIXIN_KEY_ENC_TAB)[:32]
        except Exception:
            pass

    async def init_room(self) -> bool:
        async with httpx.AsyncClient(timeout=10.0, headers=DEFAULT_HEADERS) as client:
            await self._fetch_wbi_and_buvid(client)

            # 同步 Cookie 到 WebSocket 连接 Session
            if self._session and not self._session.closed:
                cookie_parts = []
                if self._buvid3:
                    cookie_parts.append(f"buvid3={self._buvid3}")
                if self._sessdata:
                    cookie_parts.append(f"SESSDATA={self._sessdata}")
                if cookie_parts:
                    self._session.headers["Cookie"] = "; ".join(cookie_parts)

            # 1. 获取真实房间号与主播 UID
            try:
                res = await client.get(
                    f"https://api.live.bilibili.com/room/v1/Room/get_info?room_id={self._tmp_room_id}"
                )
                if res.status_code == 200:
                    data = res.json()
                    if data.get("code") == 0 and data.get("data"):
                        d = data["data"]
                        self._room_id = int(d.get("room_id") or self._tmp_room_id)
                        self._room_short_id = int(d.get("short_id") or 0)
                        self._room_owner_uid = int(d.get("uid") or 0)
            except Exception as e:
                await self._emit_log("WARN", "BILI", f"房间初始化异常: {e}")

            if not self._room_id:
                self._room_id = int(self._tmp_room_id)
                self._room_short_id = 0
                self._room_owner_uid = 0

            # 2. 通过 WBI 签名请求弹幕服务器节点与认证 Token
            try:
                base_params = {"id": self._room_id, "type": 0, "web_location": "444.8"}
                params = (
                    _sign_wbi(base_params, self._mixin_key)
                    if self._mixin_key
                    else base_params
                )
                dm_res = await client.get(
                    "https://api.live.bilibili.com/xlive/web-room/v1/index/getDanmuInfo",
                    params=params,
                )
                if dm_res.status_code == 200:
                    dm_data = dm_res.json()
                    if dm_data.get("code") == 0 and dm_data.get("data"):
                        self._host_server_list = dm_data["data"].get("host_list") or blivedm.client.DEFAULT_DANMAKU_SERVER_LIST
                        self._host_server_token = dm_data["data"].get("token")
                        return True
                    else:
                        await self._emit_log(
                            "WARN",
                            "BILI",
                            f"获取弹幕节点返回 code={dm_data.get('code')} msg={dm_data.get('message')}",
                        )
            except Exception as e:
                await self._emit_log("WARN", "BILI", f"获取弹幕节点异常: {e}")

        # 若未成功获取到 Token，禁止无 Token 连接（B站将直接拒绝握手断开连接）
        if not self._host_server_token:
            self._host_server_list = blivedm.client.DEFAULT_DANMAKU_SERVER_LIST
            self._host_server_token = None
            await self._emit_log(
                "ERROR",
                "BILI",
                "未能获取有效的弹幕认证 Token (可能由于 B站 -352 风控或网络异常)，中止连接",
            )
            return False

        return True

    async def _send_auth(self):
        auth_params: Dict[str, Any] = {
            "uid": self._uid,
            "roomid": self._room_id,
            "protover": 2,
            "platform": "web",
            "type": 2,
        }
        if self._buvid3:
            auth_params["buvid"] = self._buvid3
        if self._host_server_token:
            auth_params["key"] = self._host_server_token
        await self._websocket.send_bytes(
            self._make_packet(auth_params, blivedm.client.Operation.AUTH)
        )

    async def _parse_business_message(self, header: blivedm.client.HeaderTuple, body: bytes):
        op = header.operation
        if op == blivedm.client.Operation.SEND_MSG_REPLY:
            if header.ver == blivedm.client.ProtoVer.BROTLI:
                decompressed = await asyncio.get_running_loop().run_in_executor(
                    None, brotli.decompress, body
                )
                await self._parse_ws_message(decompressed)
            elif header.ver == blivedm.client.ProtoVer.DEFLATE:
                decompressed = await asyncio.get_running_loop().run_in_executor(
                    None, zlib.decompress, body
                )
                await self._parse_ws_message(decompressed)
            elif header.ver == blivedm.client.ProtoVer.NORMAL:
                if len(body) != 0:
                    cmd_obj = json.loads(body.decode("utf-8"))
                    await self._handle_command(cmd_obj)
        elif op == blivedm.client.Operation.AUTH_REPLY:
            reply_obj = json.loads(body.decode("utf-8"))
            if reply_obj.get("code") != blivedm.client.AuthReplyCode.OK:
                await self._emit_log("ERROR", "BILI", f"弹幕服务器认证失败: {reply_obj}")
                raise blivedm.client.AuthError(f"auth reply error: {reply_obj}")
            await self._emit_log(
                "INFO",
                "BILI",
                f"弹幕服务器 WebSocket 握手认证成功 (房间 {self._room_id})，正在实时监听弹幕...",
            )
            await self._websocket.send_bytes(
                self._make_packet({}, blivedm.client.Operation.HEARTBEAT)
            )


class BiliHandler(blivedm.BaseHandler):
    def __init__(
        self,
        callback: Callable[[DanmuEvent], Any],
        log_cb: Optional[Callable[[str, str, str], Any]] = None,
    ):
        super().__init__()
        self.callback = callback
        self.log_cb = log_cb
        self._heartbeat_logged = False

    async def _on_heartbeat(
        self, client: blivedm.BLiveClient, message: blivedm.HeartbeatMessage
    ):
        if not self._heartbeat_logged and self.log_cb:
            self._heartbeat_logged = True
            await self.log_cb(
                "INFO", "BILI", f"收到直播间心跳回包 (当前人气值: {message.popularity})"
            )

    async def handle(self, client: blivedm.BLiveClient, command: dict):
        cmd = command.get("cmd", "")
        pos = cmd.find(":")
        if pos != -1:
            cmd = cmd[:pos]
        if self.log_cb and cmd not in ("_HEARTBEAT", "WATCHED_CHANGE", "ONLINE_RANK_COUNT", "POPULARITY_CHANGE"):
            await self.log_cb("INFO", "BILI_RAW", f"收到服务器事件: {cmd}")
        if cmd == "INTERACT_WORD":
            try:
                data = command.get("data") or {}
                uname = data.get("uname") or ""
                if not uname:
                    return
                msg_type = data.get("msg_type", 1)
                fans_medal = data.get("fans_medal") or {}
                badge_name = str(fans_medal.get("medal_name") or "")
                badge_level = int(fans_medal.get("medal_level") or 0)
                action_desc = "进入了直播间" if msg_type == 1 else "关注了主播"
                if self.log_cb:
                    await self.log_cb("INFO", "WELCOME", f"[{uname}] {action_desc}")
                event = DanmuEvent(
                    uid=int(data.get("uid") or 0),
                    uname=uname,
                    content=f"【{action_desc}】",
                    badge_name=badge_name,
                    badge_level=badge_level,
                    price=0.0,
                    is_super_chat=False,
                )
                await self.callback(event)
            except Exception as e:
                if self.log_cb:
                    await self.log_cb("WARN", "BILI", f"解析进房互动异常: {e}")
            return

        if cmd == "DANMU_MSG":
            info = command.get("info") or []
            try:
                content = str(info[1]) if len(info) > 1 else ""
                user_arr = info[2] if len(info) > 2 and isinstance(info[2], list) else []
                uid = int(user_arr[0]) if len(user_arr) > 0 and user_arr[0] else 0
                uname = str(user_arr[1]) if len(user_arr) > 1 and user_arr[1] else "匿名观众"
                # 尝试从 info[0][15].user.base.name 获取完整昵称
                if len(info) > 0 and isinstance(info[0], list) and len(info[0]) > 15 and isinstance(info[0][15], dict):
                    u_base = (info[0][15].get("user") or {}).get("base") or {}
                    if u_base.get("name"):
                        uname = str(u_base["name"])
                medal_arr = info[3] if len(info) > 3 and isinstance(info[3], list) else []
                badge_level = int(medal_arr[0]) if len(medal_arr) > 0 and medal_arr[0] else 0
                badge_name = str(medal_arr[1]) if len(medal_arr) > 1 and medal_arr[1] else ""
                if not uid:
                    uid = abs(hash(uname)) % 10000000 + 1
                event = DanmuEvent(
                    uid=uid,
                    uname=uname,
                    content=content,
                    badge_name=badge_name,
                    badge_level=badge_level,
                    price=0.0,
                    is_super_chat=False,
                )
                if self.log_cb:
                    await self.log_cb("INFO", "DANMU", f"[{event.uname}] {event.content}")
                await self.callback(event)
            except Exception as e:
                if self.log_cb:
                    await self.log_cb("WARN", "BILI", f"解析弹幕异常: {e}")
            return
        await super().handle(client, command)

    async def _on_super_chat(
        self, client: blivedm.BLiveClient, message: blivedm.SuperChatMessage
    ):
        event = DanmuEvent(
            uid=int(message.uid or 0),
            uname=message.uname or "土豪观众",
            content=message.message or "",
            price=float(message.price or 0.0),
            is_super_chat=True,
        )
        if self.log_cb:
            await self.log_cb(
                "WARN", "SUPERCHAT", f"￥{event.price} [{event.uname}] {event.content}"
            )
        await self.callback(event)

    async def _on_gift(self, client: blivedm.BLiveClient, message: blivedm.GiftMessage):
        price = (
            message.total_coin / 1000.0
            if (message.coin_type == "gold" and message.total_coin > 0)
            else 0.0
        )
        event = DanmuEvent(
            uid=int(message.uid or 0),
            uname=message.uname or "热心观众",
            content=f"送出礼物【{message.gift_name}】x{message.num}",
            price=price,
            is_super_chat=False,
        )
        if self.log_cb:
            await self.log_cb(
                "INFO",
                "GIFT",
                f"[{event.uname}] 赠送 {message.gift_name} x{message.num}"
                + (f" (￥{price:.1f})" if price > 0 else ""),
            )
        await self.callback(event)


class BiliClientWrapper:
    def __init__(
        self,
        room_id: int,
        on_danmu: Callable[[DanmuEvent], Any],
        log_cb: Optional[Callable[[str, str, str], Any]] = None,
        sessdata: str = "",
    ):
        self.raw_room_id = room_id
        self.real_room_id = room_id
        self.on_danmu = on_danmu
        self.log_cb = log_cb
        self.sessdata = sessdata
        self.bili_client: Optional[WbiBLiveClient] = None
        self.is_running = False
        self.room_info: Dict[str, Any] = {}

    async def resolve_real_room_id(self, target_id: Optional[int] = None) -> int:
        query_id = target_id or self.raw_room_id
        try:
            async with httpx.AsyncClient(timeout=5.0, headers=DEFAULT_HEADERS) as client:
                res = await client.get(
                    f"https://api.live.bilibili.com/room/v1/Room/get_info?room_id={query_id}"
                )
                if res.status_code == 200:
                    data = res.json()
                    if data.get("code") == 0 and data.get("data"):
                        real_id = int(data["data"]["room_id"])
                        if not target_id:
                            self.real_room_id = real_id
                        return real_id
        except Exception as e:
            if self.log_cb:
                await self.log_cb("WARN", "BILI", f"换算房间号失败: {e}")
        return int(query_id)

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
            "cover": "",
        }
        try:
            async with httpx.AsyncClient(timeout=5.0, headers=DEFAULT_HEADERS) as client:
                res = await client.get(
                    f"https://api.live.bilibili.com/room/v1/Room/get_info?room_id={real_id}"
                )
                if res.status_code == 200:
                    data = res.json()
                    if data.get("code") == 0 and data.get("data"):
                        d = data["data"]
                        info["title"] = d.get("title", "")
                        info["live_status"] = d.get("live_status", 0)
                        info["area_name"] = d.get("area_name", "")
                        info["online"] = d.get("online", 0)
                        info["cover"] = d.get("user_cover", "")

                u_res = await client.get(
                    f"https://api.live.bilibili.com/live_user/v1/UserInfo/get_anchor_in_room?roomid={real_id}"
                )
                if u_res.status_code == 200:
                    u_data = u_res.json()
                    if u_data.get("code") == 0 and u_data.get("data"):
                        info["uname"] = (u_data["data"].get("info") or {}).get(
                            "uname", ""
                        )
        except Exception as e:
            if self.log_cb:
                await self.log_cb("WARN", "BILI", f"获取房间信息异常: {e}")

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
            self.bili_client = WbiBLiveClient(
                self.real_room_id,
                sessdata=self.sessdata,
                log_cb=self.log_cb,
                ssl=True,
            )
            init_ok = await self.bili_client.init_room()
            if not init_ok:
                await self.bili_client.close()
                self.bili_client = None
                self.is_running = False
                if self.log_cb:
                    await self.log_cb("ERROR", "BILI", f"直播间 [{self.real_room_id}] 认证节点初始化失败")
                return False

            handler = BiliHandler(self.on_danmu, self.log_cb)
            self.bili_client.add_handler(handler)
            self.bili_client.start()
            self.is_running = True
            if self.log_cb:
                await self.log_cb(
                    "INFO",
                    "BILI",
                    f"正在连接 B站 WebSocket 直播间 [{self.real_room_id}] (主播: {self.room_info.get('uname', '未知')})",
                )
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
        running = bool(
            self.is_running
            and self.bili_client is not None
            and self.bili_client.is_running
        )
        self.is_running = running
        return {
            "is_running": running,
            "raw_room_id": self.raw_room_id,
            "real_room_id": self.real_room_id,
            "room_info": self.room_info,
        }

    async def inject_mock_danmu(
        self, uname: str, content: str, price: float = 0.0, is_sc: bool = False
    ):
        event = DanmuEvent(
            uid=int(time.time() * 1000) % 10000000 + 1000,
            uname=uname,
            content=content,
            badge_name="粉丝团",
            badge_level=15,
            price=price,
            is_super_chat=is_sc,
        )
        if self.log_cb:
            tag = "MOCK_SC" if is_sc else "MOCK_DANMU"
            await self.log_cb("INFO", tag, f"[{uname}] {content}")
        await self.on_danmu(event)
