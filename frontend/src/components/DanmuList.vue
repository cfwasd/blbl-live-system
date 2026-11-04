<template>
  <div class="danmu-container">
    <transition-group name="danmu-fade" tag="div" class="danmu-list">
      <div v-for="item in visibleDanmu" :key="item.id" class="danmu-item">
        <span v-if="item.badge" class="badge">Lv{{ item.level }} {{ item.badge }}</span>
        <span class="uname">{{ item.uname }}:</span>
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
  width: 420px;
  height: 380px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}
.danmu-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.danmu-item {
  background: rgba(15, 23, 42, 0.65);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  padding: 6px 12px;
  border-radius: 12px;
  font-size: 14px;
  color: #fff;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.badge {
  background: linear-gradient(135deg, #06b6d4, #3b82f6);
  color: #fff;
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 6px;
}
.uname { color: #38bdf8; font-weight: 600; }
.danmu-fade-enter-active { transition: all 0.3s ease-out; }
.danmu-fade-enter-from { opacity: 0; transform: translateY(15px); }
</style>
