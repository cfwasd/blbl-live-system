<template>
  <div class="danmu-container">
    <transition-group name="danmu-fade" tag="div" class="danmu-list">
      <div v-for="item in visibleDanmu" :key="item.id" class="danmu-item" :class="{ 'is-vip': (item.level || 0) >= 15 }">
        <!-- 粉丝勋章 -->
        <span v-if="item.badge" class="badge" :class="'badge-tier-' + Math.min(3, Math.floor((item.level || 0) / 10))">
          <span class="badge-level">{{ item.level }}</span>
          <span class="badge-name">{{ item.badge }}</span>
        </span>

        <!-- 昵称与正文 -->
        <span class="uname">{{ item.uname }}</span>
        <span class="colon">:</span>
        <span class="content">{{ item.content }}</span>
      </div>
    </transition-group>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

interface DanmuMsg {
  id: string;
  uname: string;
  content: string;
  badge?: string;
  level?: number;
}

const visibleDanmu = ref<DanmuMsg[]>([]);

const addDanmu = (msg: DanmuMsg) => {
  visibleDanmu.value.push(msg);
  // 固定滑窗上限 30 条，超出即刻移除，防止长时开播 DOM 泄漏
  if (visibleDanmu.value.length > 30) {
    visibleDanmu.value.shift();
  }
};

defineExpose({ addDanmu });
</script>

<style scoped>
.danmu-container {
  width: 460px;
  height: 420px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  pointer-events: none;
}
.danmu-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-bottom: 8px;
}
.danmu-item {
  background: rgba(11, 15, 25, 0.75);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
  padding: 8px 14px;
  border-radius: 14px;
  font-size: 14px;
  color: #f8fafc;
  display: inline-flex;
  align-items: center;
  align-self: flex-start;
  max-width: 100%;
  line-height: 1.4;
  word-break: break-all;
}
.is-vip {
  border-color: rgba(234, 179, 8, 0.35);
  box-shadow: 0 4px 20px rgba(234, 179, 8, 0.15);
}
.badge {
  display: inline-flex;
  align-items: center;
  border-radius: 6px;
  overflow: hidden;
  font-size: 10px;
  font-weight: 800;
  margin-right: 8px;
  flex-shrink: 0;
}
.badge-tier-0 { background: #3b82f6; }
.badge-tier-1 { background: #8b5cf6; }
.badge-tier-2 { background: #ec4899; }
.badge-tier-3 { background: linear-gradient(135deg, #f59e0b, #ef4444); }

.badge-level {
  background: rgba(0, 0, 0, 0.25);
  padding: 1px 5px;
  color: #fff;
}
.badge-name {
  padding: 1px 6px;
  color: #fff;
}
.uname {
  color: #38bdf8;
  font-weight: 700;
  text-shadow: 0 1px 2px rgba(0,0,0,0.4);
}
.colon {
  color: #94a3b8;
  margin: 0 4px 0 1px;
}
.content {
  color: #f1f5f9;
  font-weight: 500;
  text-shadow: 0 1px 2px rgba(0,0,0,0.5);
}
.danmu-fade-enter-active {
  transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}
.danmu-fade-enter-from {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}
.danmu-fade-leave-active {
  transition: all 0.2s ease-in;
}
.danmu-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
