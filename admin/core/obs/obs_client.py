from admin.config import OBSConfig

class OBSClientWrapper:
    def __init__(self, config: OBSConfig):
        self.config = config
        self.client = None
        self.is_connected = False

    def connect(self) -> bool:
        try:
            import obsws_python as obs
            self.client = obs.ReqClient(
                host=self.config.host,
                port=self.config.port,
                password=self.config.password,
                timeout=3
            )
            self.is_connected = True
            return True
        except Exception:
            try:
                import obswebsocket, obswebsocket.requests
                self.client = obswebsocket.obsws(
                    self.config.host,
                    self.config.port,
                    self.config.password
                )
                self.client.connect()
                self.is_connected = True
                return True
            except Exception:
                self.is_connected = False
                return False

    def start_streaming(self) -> bool:
        if not self.is_connected and not self.connect():
            return False
        try:
            if hasattr(self.client, "start_stream"):
                self.client.start_stream()
                return True
            import obswebsocket.requests
            self.client.call(obswebsocket.requests.StartStreaming())
            return True
        except Exception:
            return False

    def stop_streaming(self) -> bool:
        if not self.is_connected and not self.connect():
            return False
        try:
            if hasattr(self.client, "stop_stream"):
                self.client.stop_stream()
                return True
            import obswebsocket.requests
            self.client.call(obswebsocket.requests.StopStreaming())
            return True
        except Exception:
            return False

    def get_status(self) -> dict:
        if not self.is_connected and not self.connect():
            return {"connected": False, "streaming": False}
        try:
            if hasattr(self.client, "get_stream_status"):
                res = self.client.get_stream_status()
                return {"connected": True, "streaming": res.output_active}
            import obswebsocket.requests
            res = self.client.call(obswebsocket.requests.GetStreamStatus())
            return {"connected": True, "streaming": res.getStreaming()}
        except Exception:
            return {"connected": False, "streaming": False}
