<template>
  <div class="sc-container" v-if="activeSCs.length > 0">
    <transition-group name="sc-slide" tag="div" class="sc-list">
      <div v-for="sc in activeSCs" :key="sc.id" class="sc-card">
        <!-- 头部：金额与打赏者 -->
        <div class="sc-header">
          <div class="donor-info">
            <span class="sc-icon">💎</span>
            <span class="donor-name">{{ sc.uname }}</span>
          </div>
          <div class="sc-price">￥{{ Number(sc.price).toFixed(1) }}</div>
        </div>

        <!-- 醒目正文 -->
        <div class="sc-body">
          {{ sc.content }}
        </div>

        <!-- 倒计时进度条 -->
        <div class="sc-timer-bar">
          <div class="sc-progress" :style="{ width: sc.progress + '%' }"></div>
        </div>
      </div>
    </transition-group>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

interface SCItem {
  id: string;
  uname: string;
  price: number;
  content: string;
  duration: number;
  progress: number;
  timer?: any;
}

const activeSCs = ref<SCItem[]>([]);

const addSC = (data: { id?: string; uname: string; price: number; content: string; duration?: number }) => {
  const duration = data.duration || 60;
  const item: SCItem = {
    id: data.id || ('sc_' + Date.now()),
    uname: data.uname,
    price: data.price,
    content: data.content,
    duration: duration,
    progress: 100
  };

  const startTime = Date.now();
  item.timer = setInterval(() => {
    const elapsed = (Date.now() - startTime) / 1000;
    const remaining = Math.max(0, 100 - (elapsed / duration) * 100);
    item.progress = remaining;
    if (remaining <= 0) {
      clearInterval(item.timer);
      activeSCs.value = activeSCs.value.filter(x => x.id !== item.id);
    }
  }, 100);

  activeSCs.value.unshift(item);
  if (activeSCs.value.length > 3) {
    const removed = activeSCs.value.pop();
    if (removed?.timer) clearInterval(removed.timer);
  }
};

defineExpose({ addSC });
</script>

<style scoped>
.sc-container {
  display: flex;
  justify-content: center;
  position: absolute;
  top: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 50;
  width: 500px;
}
.sc-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}
.sc-card {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.9) 0%, rgba(225, 29, 72, 0.95) 100%);
  border-radius: 16px;
  padding: 12px 16px;
  box-shadow: 0 10px 30px rgba(245, 158, 11, 0.4), inset 0 1px 1px rgba(255, 255, 255, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(12px);
  color: #fff;
  position: relative;
  overflow: hidden;
}
.sc-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.donor-info {
  display: flex;
  align-items: center;
  gap: 6px;
}
.sc-icon { font-size: 16px; }
.donor-name { font-weight: 800; font-size: 14px; text-shadow: 0 1px 2px rgba(0,0,0,0.3); }
.sc-price {
  font-family: monospace;
  font-size: 16px;
  font-weight: 900;
  background: rgba(0, 0, 0, 0.25);
  padding: 2px 10px;
  border-radius: 20px;
}
.sc-body {
  font-size: 13px;
  line-height: 1.4;
  margin-bottom: 8px;
  font-weight: 500;
  text-shadow: 0 1px 2px rgba(0,0,0,0.3);
}
.sc-timer-bar {
  width: 100%;
  height: 4px;
  background: rgba(0, 0, 0, 0.25);
  border-radius: 2px;
  overflow: hidden;
}
.sc-progress {
  height: 100%;
  background: #fef08a;
  box-shadow: 0 0 8px #fef08a;
  transition: width 0.1s linear;
}
.sc-slide-enter-active { transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1); }
.sc-slide-enter-from { opacity: 0; transform: translateY(-30px) scale(0.95); }
.sc-slide-leave-active { transition: all 0.3s ease-in; }
.sc-slide-leave-to { opacity: 0; transform: translateY(-20px); }
</style>
