<template>
  <div class="emotion-heartbeat-card" :class="'status-' + currentStatus">
    <div class="heartbeat-header">
      <div class="ecg-title-wrap">
        <span class="heart-pulse-icon">💓</span>
        <span class="ecg-title">AI EMOTION & BPM</span>
      </div>
      <span class="bpm-counter">{{ currentBpm }} <span class="bpm-unit">BPM</span></span>
    </div>

    <!-- 动态跳动心电图波形 -->
    <div class="ecg-graph-wrap">
      <svg class="ecg-svg" viewBox="0 0 160 32" preserveAspectRatio="none">
        <path
          class="ecg-line"
          d="M 0 16 L 30 16 L 36 6 L 42 26 L 48 10 L 54 20 L 60 16 L 100 16 L 106 4 L 112 28 L 118 10 L 124 22 L 130 16 L 160 16"
        />
      </svg>
    </div>

    <div class="emotion-tag-row">
      <span class="status-indicator-dot"></span>
      <span class="emotion-text">{{ emotionLabel }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';

const props = defineProps<{
  isSpeaking: boolean;
  isThinking: boolean;
  expression?: string;
  motion?: string;
}>();

const baseBpm = ref(78);
let bpmTimer: any = null;

const currentStatus = computed(() => {
  if (props.isSpeaking) return 'speaking';
  if (props.isThinking) return 'thinking';
  if (props.expression === 'smile' || props.motion === 'Happy') return 'happy';
  return 'idle';
});

const currentBpm = computed(() => {
  if (currentStatus.value === 'speaking') return baseBpm.value + 24;
  if (currentStatus.value === 'happy') return baseBpm.value + 32;
  if (currentStatus.value === 'thinking') return baseBpm.value + 12;
  return baseBpm.value;
});

const emotionLabel = computed(() => {
  if (currentStatus.value === 'speaking') return '🎙️ 傲娇对话播报中';
  if (currentStatus.value === 'thinking') return '💭 灵感正在生成中';
  if (currentStatus.value === 'happy') return '✨ 收到投喂心花怒放';
  return '💖 傲娇元气待命中';
});

onMounted(() => {
  bpmTimer = setInterval(() => {
    // 随机微幅心率律动
    baseBpm.value = 76 + Math.floor(Math.random() * 6);
  }, 3000);
});

onUnmounted(() => {
  if (bpmTimer) clearInterval(bpmTimer);
});
</script>

<style scoped>
.emotion-heartbeat-card {
  width: 200px;
  background: rgba(11, 15, 25, 0.82);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(56, 189, 248, 0.25);
  border-radius: 16px;
  padding: 8px 12px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5), inset 0 0 10px rgba(56, 189, 248, 0.08);
  color: #fff;
  user-select: none;
  transition: all 0.3s ease;
}

.heartbeat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.ecg-title-wrap {
  display: flex;
  align-items: center;
  gap: 4px;
}
.heart-pulse-icon {
  font-size: 11px;
  animation: heartPulse 1.2s infinite ease-in-out;
}
@keyframes heartPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.3); }
}

.ecg-title {
  font-size: 9px;
  font-weight: 800;
  color: #94a3b8;
  letter-spacing: 0.5px;
}

.bpm-counter {
  font-family: monospace;
  font-size: 12px;
  font-weight: 800;
  color: #f43f5e;
}
.bpm-unit {
  font-size: 9px;
  color: #64748b;
}

.ecg-graph-wrap {
  width: 100%;
  height: 20px;
  overflow: hidden;
  position: relative;
}

.ecg-svg {
  width: 100%;
  height: 100%;
}

.ecg-line {
  fill: none;
  stroke: #f43f5e;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-dasharray: 200;
  stroke-dashoffset: 200;
  animation: ecgFlow 2s linear infinite;
}

@keyframes ecgFlow {
  to { stroke-dashoffset: 0; }
}

.emotion-tag-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
}

.status-indicator-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #38bdf8;
  box-shadow: 0 0 6px #38bdf8;
}

.status-speaking .status-indicator-dot {
  background: #f43f5e;
  box-shadow: 0 0 6px #f43f5e;
}
.status-thinking .status-indicator-dot {
  background: #c084fc;
  box-shadow: 0 0 6px #c084fc;
}
.status-happy .status-indicator-dot {
  background: #fbbf24;
  box-shadow: 0 0 6px #fbbf24;
}

.emotion-text {
  font-size: 10px;
  font-weight: 700;
  color: #cbd5e1;
}
</style>
