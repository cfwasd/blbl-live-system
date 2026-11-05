<template>
  <div class="danmu-wrapper">
    <!-- 弹幕墙顶部卡片标题栏 -->
    <div class="danmu-header">
      <div class="header-left">
        <span class="chat-icon">💬</span>
        <span class="chat-title">实时弹幕墙</span>
        <span class="chat-tag">LIVE CHAT</span>
      </div>
      <div class="header-right">
        <span class="pulse-green-dot"></span>
        <span class="danmu-count">{{ visibleDanmu.length }} 条</span>
      </div>
    </div>

    <!-- 弹幕滚动展示区 -->
    <div class="danmu-container" ref="containerRef">
      <div v-if="visibleDanmu.length === 0" class="empty-danmu-hint">
        ✨ 弹幕通道就绪，发送弹幕与 Gemini 娘互动吧~
      </div>
      <transition-group name="danmu-fade" tag="div" class="danmu-list">
        <div
          v-for="item in visibleDanmu"
          :key="item.id"
          class="danmu-item"
          :class="{
            'is-vip': (item.level || 0) >= 15,
            'is-gold': (item.level || 0) >= 20
          }"
        >
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
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue';

export interface DanmuMsg {
  id: string;
  uname: string;
  content: string;
  badge?: string;
  level?: number;
}

const visibleDanmu = ref<DanmuMsg[]>([]);
const containerRef = ref<HTMLDivElement | null>(null);

const addDanmu = (msg: DanmuMsg) => {
  visibleDanmu.value.push(msg);
  // 固定滑窗上限 35 条，超长展示区域
  if (visibleDanmu.value.length > 35) {
    visibleDanmu.value.shift();
  }
  nextTick(() => {
    if (containerRef.value) {
      containerRef.value.scrollTop = containerRef.value.scrollHeight;
    }
  });
};

defineExpose({ addDanmu });
</script>

<style scoped>
.danmu-wrapper {
  width: 480px;
  background: rgba(11, 15, 25, 0.85);
  backdrop-filter: blur(24px);
  border: 1.5px solid rgba(56, 189, 248, 0.28);
  border-radius: 22px;
  padding: 14px 16px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.65), inset 0 0 14px rgba(56, 189, 248, 0.08);
  user-select: none;
  pointer-events: none;
}

.danmu-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 8px;
  margin-bottom: 6px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 6px;
}
.chat-icon { font-size: 13px; }
.chat-title {
  font-size: 12px;
  font-weight: 800;
  color: #f1f5f9;
  letter-spacing: 0.5px;
}
.chat-tag {
  font-size: 9px;
  font-weight: 800;
  color: #38bdf8;
  background: rgba(56, 189, 248, 0.15);
  padding: 1px 6px;
  border-radius: 4px;
  border: 1px solid rgba(56, 189, 248, 0.25);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 5px;
}
.pulse-green-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 6px #10b981;
  animation: pulseGreen 1.6s infinite;
}
@keyframes pulseGreen {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.85); }
}
.danmu-count {
  font-family: monospace;
  font-size: 11px;
  color: #94a3b8;
  font-weight: 600;
}

.danmu-container {
  height: 400px;
  overflow-y: auto;
  scrollbar-width: none;
  display: flex;
  flex-direction: column;
}
.danmu-container::-webkit-scrollbar {
  display: none;
}

.empty-danmu-hint {
  font-size: 12px;
  color: #64748b;
  text-align: center;
  margin: auto 0;
  font-style: italic;
}

.danmu-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: auto;
}

.danmu-item {
  background: rgba(15, 23, 42, 0.78);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
  padding: 6px 12px;
  border-radius: 12px;
  font-size: 13px;
  color: #f8fafc;
  display: inline-flex;
  align-items: center;
  align-self: flex-start;
  max-width: 100%;
  line-height: 1.4;
  word-break: break-all;
  transition: all 0.2s ease;
}

.is-vip {
  border-color: rgba(56, 189, 248, 0.45);
  background: rgba(14, 165, 233, 0.16);
  box-shadow: 0 4px 15px rgba(56, 189, 248, 0.2);
}

.is-gold {
  border-color: rgba(251, 191, 36, 0.6);
  background: rgba(245, 158, 11, 0.18);
  box-shadow: 0 4px 16px rgba(245, 158, 11, 0.25);
}

.badge {
  display: inline-flex;
  align-items: center;
  border-radius: 4px;
  overflow: hidden;
  font-size: 10px;
  font-weight: 800;
  margin-right: 6px;
  flex-shrink: 0;
}
.badge-tier-0 { background: #3b82f6; }
.badge-tier-1 { background: #8b5cf6; }
.badge-tier-2 { background: #ec4899; }
.badge-tier-3 { background: linear-gradient(135deg, #f59e0b, #ef4444); }

.badge-level {
  background: rgba(0, 0, 0, 0.25);
  padding: 1px 4px;
  color: #fff;
}
.badge-name {
  padding: 1px 5px;
  color: #fff;
}

.uname {
  color: #38bdf8;
  font-weight: 700;
  text-shadow: 0 1px 2px rgba(0,0,0,0.4);
  flex-shrink: 0;
}
.is-gold .uname {
  color: #fbbf24;
}

.colon {
  color: #94a3b8;
  margin: 0 3px 0 1px;
}

.content {
  color: #f1f5f9;
  font-weight: 500;
  text-shadow: 0 1px 2px rgba(0,0,0,0.5);
}

.danmu-fade-enter-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.danmu-fade-enter-from {
  opacity: 0;
  transform: translateY(16px) scale(0.96);
}
.danmu-fade-leave-active {
  transition: all 0.15s ease-in;
}
.danmu-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
