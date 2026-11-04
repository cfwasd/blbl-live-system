import time
from cachetools import TTLCache

class UIDCooldownManager:
    def __init__(self, ttl_seconds: float = 10.0):
        # 最大缓存 10000 个活跃用户，自动过期杜绝内存膨胀
        self.cache = TTLCache(maxsize=10000, ttl=ttl_seconds)

    def check_and_update(self, uid: int) -> bool:
        now = time.time()
        if uid in self.cache:
            return False
        self.cache[uid] = now
        return True
