<template>
  <div class="welcome-banner-anchor">
    <transition-group name="welcome-bounce" tag="div" class="welcome-list">
      <div v-for="item in activeWelcomes" :key="item.id" class="welcome-card">
        <!-- 装饰猫耳 -->
        <div class="cat-ear ear-left"></div>
        <div class="cat-ear ear-right"></div>

        <div class="welcome-body">
          <span class="welcome-paw">🐾</span>
          <div class="welcome-text-wrap">
            <span class="welcome-prefix">欢迎</span>
            <span v-if="item.badge" class="fan-badge">
              <span class="badge-lvl">{{ item.level }}</span>
              <span class="badge-title">{{ item.badge }}</span>
            </span>
            <span class="viewer-name">@{{ item.uname }}</span>
            <span class="welcome-suffix">降临直播间，随便坐坐吧~</span>
          </div>
          <span class="welcome-sparkle">✨</span>
        </div>
      </div>
    </transition-group>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

export interface WelcomeItem {
  id: string;
  uname: string;
  badge?: string;
  level?: number;
}

const activeWelcomes = ref<WelcomeItem[]>([]);

const addWelcome = (data: { uname: string; badge?: string; level?: number }) => {
  const item: WelcomeItem = {
    id: 'w_' + Date.now() + '_' + Math.random().toString(36).substr(2, 4),
    uname: data.uname,
    badge: data.badge,
    level: data.level
  };

  activeWelcomes.value.push(item);
  if (activeWelcomes.value.length > 3) {
    activeWelcomes.value.shift();
  }

  setTimeout(() => {
    activeWelcomes.value = activeWelcomes.value.filter(x => x.id !== item.id);
  }, 4500);
};

defineExpose({ addWelcome });
</script>

<style scoped>
.welcome-banner-anchor {
  position: absolute;
  top: 130px;
  left: 28px;
  z-index: 45;
  pointer-events: none;
  user-select: none;
}

.welcome-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.welcome-card {
  position: relative;
  background: linear-gradient(135deg, rgba(30, 27, 75, 0.92) 0%, rgba(88, 28, 135, 0.92) 100%);
  border: 1.5px solid rgba(236, 72, 153, 0.6);
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.55), 0 0 16px rgba(236, 72, 153, 0.35);
  border-radius: 20px;
  padding: 8px 18px 8px 14px;
  color: #fff;
  display: inline-flex;
  align-items: center;
  max-width: 480px;
}

/* 萌系全息猫耳 */
.cat-ear {
  position: absolute;
  top: -8px;
  width: 0;
  height: 0;
  border-left: 7px solid transparent;
  border-right: 7px solid transparent;
  border-bottom: 9px solid rgba(236, 72, 153, 0.85);
  filter: drop-shadow(0 -2px 4px rgba(236, 72, 153, 0.5));
}
.ear-left { left: 16px; transform: rotate(-15deg); }
.ear-right { left: 34px; transform: rotate(15deg); }

.welcome-body {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12.5px;
}

.welcome-paw {
  font-size: 15px;
  animation: pawWave 1.4s infinite ease-in-out;
}
@keyframes pawWave {
  0%, 100% { transform: rotate(0deg) scale(1); }
  50% { transform: rotate(15deg) scale(1.2); }
}

.welcome-text-wrap {
  display: flex;
  align-items: center;
  gap: 5px;
  white-space: nowrap;
}

.welcome-prefix, .welcome-suffix {
  color: #f1f5f9;
  font-weight: 600;
}

.viewer-name {
  color: #fbcfe8;
  font-weight: 800;
  text-shadow: 0 0 8px rgba(244, 114, 182, 0.6);
}

.welcome-sparkle {
  font-size: 13px;
  color: #fbbf24;
  animation: sparkleTwinkle 1s infinite alternate;
}
@keyframes sparkleTwinkle {
  0% { transform: scale(0.8); opacity: 0.6; }
  100% { transform: scale(1.3); opacity: 1; }
}

.fan-badge {
  display: inline-flex;
  align-items: center;
  font-size: 10px;
  font-weight: 800;
  background: linear-gradient(135deg, #ec4899, #8b5cf6);
  border-radius: 4px;
  overflow: hidden;
  margin: 0 2px;
}
.badge-lvl { background: rgba(0, 0, 0, 0.3); padding: 1px 4px; }
.badge-title { padding: 1px 5px; }

/* 进出场动画 */
.welcome-bounce-enter-active {
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.welcome-bounce-leave-active {
  transition: all 0.3s ease-in;
}
.welcome-bounce-enter-from {
  opacity: 0;
  transform: translateX(-30px) scale(0.9);
}
.welcome-bounce-leave-to {
  opacity: 0;
  transform: translateY(-10px) scale(0.9);
}
</style>
