<template>
  <div class="stream-goal-card">
    <div class="goal-header">
      <div class="goal-title-wrap">
        <span class="goal-icon">🎯</span>
        <span class="goal-label">本场互动能量</span>
        <span class="goal-badge">GOAL</span>
      </div>
      <div class="goal-values">
        <span class="current-val">{{ currentCount }}</span>
        <span class="target-val">/ {{ targetCount }} 条</span>
      </div>
    </div>

    <!-- 动态充能能量条 -->
    <div class="goal-track">
      <div
        class="goal-fill"
        :style="{ width: percent + '%' }"
      >
        <span class="fill-light"></span>
      </div>
    </div>

    <div class="goal-footer">
      <span class="goal-sub">💖 达成率 {{ percent }}%</span>
      <span class="goal-hint">弹幕互动与点歌皆可充能</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = withDefaults(defineProps<{
  currentCount?: number;
  targetCount?: number;
}>(), {
  currentCount: 0,
  targetCount: 100
});

const percent = computed(() => {
  if (props.targetCount <= 0) return 100;
  return Math.min(100, Math.floor((props.currentCount / props.targetCount) * 100));
});
</script>

<style scoped>
.stream-goal-card {
  width: 310px;
  background: rgba(11, 15, 25, 0.82);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(56, 189, 248, 0.25);
  border-radius: 16px;
  padding: 10px 14px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), inset 0 0 10px rgba(56, 189, 248, 0.08);
  color: #fff;
  user-select: none;
}

.goal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.goal-title-wrap {
  display: flex;
  align-items: center;
  gap: 5px;
}
.goal-icon { font-size: 13px; }
.goal-label {
  font-size: 11px;
  font-weight: 800;
  color: #f1f5f9;
  letter-spacing: 0.5px;
}
.goal-badge {
  font-size: 9px;
  font-weight: 800;
  color: #fbbf24;
  background: rgba(251, 191, 36, 0.15);
  padding: 1px 5px;
  border-radius: 4px;
  border: 1px solid rgba(251, 191, 36, 0.3);
}

.goal-values {
  font-family: monospace;
  font-size: 12px;
}
.current-val {
  font-weight: 800;
  color: #38bdf8;
  font-size: 13px;
}
.target-val {
  color: #64748b;
  font-size: 11px;
}

.goal-track {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  overflow: hidden;
  position: relative;
  box-shadow: inset 0 1px 2px rgba(0,0,0,0.5);
}

.goal-fill {
  height: 100%;
  background: linear-gradient(90deg, #06b6d4, #8b5cf6, #ec4899);
  border-radius: 6px;
  box-shadow: 0 0 10px rgba(139, 92, 246, 0.6);
  position: relative;
  transition: width 0.4s ease;
}

.fill-light {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 8px;
  background: #fff;
  border-radius: 50%;
  filter: blur(2px);
  opacity: 0.8;
}

.goal-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 5px;
  font-size: 10px;
}
.goal-sub {
  color: #c084fc;
  font-weight: 700;
}
.goal-hint {
  color: #64748b;
}
</style>
