<template>
  <transition name="topic-slide">
    <div
      v-if="visible && topic && topic.question"
      class="current-topic-banner"
      :class="{ 'is-sc': topic.is_super_chat, 'is-thinking': isThinking && !isSpeaking }"
    >
      <!-- 装饰背景全息微光与角标 -->
      <div class="holo-corner top-left"></div>
      <div class="holo-corner top-right"></div>
      <div class="holo-corner bottom-left"></div>
      <div class="holo-corner bottom-right"></div>

      <!-- 头部：状态标识 + 提问者信息 -->
      <div class="topic-header">
        <div class="topic-badge">
          <span class="live-pulse-dot" :class="{ 'dot-thinking': isThinking && !isSpeaking }"></span>
          <span class="badge-title">
            {{ topic.is_super_chat ? '🔥 优先答谢 SC 醒目留言' : (isThinking && !isSpeaking ? '💭 正在思考回复提问' : '💬 正在语音回复') }}
          </span>
        </div>

        <div class="asker-info">
          <!-- 粉丝牌 -->
          <span v-if="topic.badge" class="fan-badge" :class="'tier-' + Math.min(3, Math.floor((topic.level || 0) / 10))">
            <span class="fan-lvl">{{ topic.level }}</span>
            <span class="fan-name">{{ topic.badge }}</span>
          </span>

          <span class="asker-name">@{{ topic.uname }}</span>
          <span v-if="topic.is_super_chat" class="sc-price-tag">￥{{ Number(topic.price || 0).toFixed(1) }}</span>
        </div>
      </div>

      <!-- 提问内容正文 (长文字自适应排版) -->
      <div class="topic-body" :class="questionSizeClass">
        <span class="quote-mark">“</span>
        <span class="question-text">{{ topic.question }}</span>
        <span class="quote-mark">”</span>
      </div>

      <!-- 底部动态指示条 -->
      <div class="topic-footer-bar">
        <div v-if="isThinking && !isSpeaking" class="thinking-dots-anim">
          <span class="think-dot td-1"></span>
          <span class="think-dot td-2"></span>
          <span class="think-dot td-3"></span>
          <span class="talking-hint">Gemini 娘正在组织语言中...</span>
        </div>
        <div v-else class="talking-wave-anim">
          <div class="sound-wave-mini">
            <span class="wave-bar w-1"></span>
            <span class="wave-bar w-2"></span>
            <span class="wave-bar w-3"></span>
            <span class="wave-bar w-4"></span>
            <span class="wave-bar w-5"></span>
            <span class="wave-bar w-6"></span>
            <span class="wave-bar w-7"></span>
          </div>
          <span class="talking-hint">Gemini 娘正在语音回答中...</span>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';

export interface TopicData {
  uname: string;
  question: string;
  badge?: string;
  level?: number;
  is_super_chat?: boolean;
  price?: number;
}

const props = withDefaults(defineProps<{
  active: boolean;
  isThinking?: boolean;
  isSpeaking?: boolean;
  topic: TopicData | null;
}>(), {
  active: false,
  isThinking: false,
  isSpeaking: false,
  topic: null
});

const visible = ref(false);
let hideTimer: any = null;

const questionSizeClass = computed(() => {
  const len = props.topic?.question?.length || 0;
  if (len > 60) return 'q-dense';
  if (len > 30) return 'q-medium';
  return 'q-normal';
});

watch([() => props.active, () => props.isThinking, () => props.isSpeaking, () => props.topic], ([active, thinking, speaking, currentTopic]) => {
  const isBusy = active || thinking || speaking;
  if (isBusy && currentTopic && currentTopic.question) {
    if (hideTimer) clearTimeout(hideTimer);
    visible.value = true;
  } else if (!isBusy) {
    // 互动结束后延时 2.5 秒收起
    if (hideTimer) clearTimeout(hideTimer);
    hideTimer = setTimeout(() => {
      visible.value = false;
    }, 2500);
  }
}, { immediate: true });
</script>

<style scoped>
.current-topic-banner {
  position: relative;
  background: rgba(11, 15, 25, 0.92);
  backdrop-filter: blur(24px);
  border: 1.5px solid rgba(56, 189, 248, 0.5);
  border-radius: 18px;
  padding: 12px 18px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.7), 0 0 24px rgba(56, 189, 248, 0.25);
  width: 480px;
  max-width: 480px;
  color: #fff;
  overflow: hidden;
  user-select: none;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.is-thinking {
  border-color: rgba(192, 132, 252, 0.6);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.7), 0 0 24px rgba(192, 132, 252, 0.3);
}

.is-sc {
  background: linear-gradient(135deg, rgba(30, 20, 10, 0.94) 0%, rgba(20, 10, 25, 0.96) 100%);
  border-color: rgba(251, 191, 36, 0.7);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.7), 0 0 28px rgba(251, 191, 36, 0.4);
}

/* 赛博角标装饰 */
.holo-corner {
  position: absolute;
  width: 6px;
  height: 6px;
  border-color: #38bdf8;
  pointer-events: none;
}
.is-thinking .holo-corner { border-color: #c084fc; }
.is-sc .holo-corner { border-color: #fbbf24; }

.top-left { top: 3px; left: 3px; border-top: 2px solid; border-left: 2px solid; }
.top-right { top: 3px; right: 3px; border-top: 2px solid; border-right: 2px solid; }
.bottom-left { bottom: 3px; left: 3px; border-bottom: 2px solid; border-left: 2px solid; }
.bottom-right { bottom: 3px; right: 3px; border-bottom: 2px solid; border-right: 2px solid; }

.topic-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  gap: 12px;
}

.topic-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(56, 189, 248, 0.15);
  padding: 3px 10px;
  border-radius: 20px;
  border: 1px solid rgba(56, 189, 248, 0.3);
}
.is-thinking .topic-badge {
  background: rgba(192, 132, 252, 0.2);
  border-color: rgba(192, 132, 252, 0.4);
}
.is-sc .topic-badge {
  background: rgba(251, 191, 36, 0.2);
  border-color: rgba(251, 191, 36, 0.4);
}

.live-pulse-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #38bdf8;
  box-shadow: 0 0 8px #38bdf8;
  animation: pulseDot 1.2s infinite;
}
.dot-thinking {
  background: #c084fc;
  box-shadow: 0 0 8px #c084fc;
  animation: pulseDot 0.8s infinite;
}
.is-sc .live-pulse-dot {
  background: #fbbf24;
  box-shadow: 0 0 8px #fbbf24;
}

@keyframes pulseDot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.3; transform: scale(0.8); }
}

.badge-title {
  font-size: 11px;
  font-weight: 800;
  color: #38bdf8;
  letter-spacing: 0.5px;
}
.is-thinking .badge-title { color: #e9d5ff; }
.is-sc .badge-title { color: #fbbf24; }

.asker-info {
  display: flex;
  align-items: center;
  gap: 6px;
  max-width: 58%;
  overflow: hidden;
}

.asker-name {
  font-size: 13px;
  font-weight: 700;
  color: #f1f5f9;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.is-sc .asker-name { color: #fef08a; }

.sc-price-tag {
  font-size: 12px;
  font-weight: 900;
  color: #fbbf24;
  background: rgba(251, 191, 36, 0.2);
  padding: 1px 6px;
  border-radius: 6px;
  border: 1px solid rgba(251, 191, 36, 0.4);
}

.fan-badge {
  display: inline-flex;
  align-items: center;
  font-size: 10px;
  font-weight: 800;
  border-radius: 4px;
  overflow: hidden;
  flex-shrink: 0;
}
.tier-0 { background: #3b82f6; }
.tier-1 { background: #8b5cf6; }
.tier-2 { background: #ec4899; }
.tier-3 { background: linear-gradient(135deg, #f59e0b, #ef4444); }
.fan-lvl { background: rgba(0, 0, 0, 0.25); padding: 1px 4px; }
.fan-name { padding: 1px 5px; }

.topic-body {
  font-weight: 600;
  line-height: 1.45;
  color: #f8fafc;
  margin-bottom: 8px;
  word-break: break-all;
  max-height: 80px;
  overflow-y: auto;
  scrollbar-width: none;
}
.topic-body::-webkit-scrollbar {
  display: none;
}
.q-normal { font-size: 14px; }
.q-medium { font-size: 12.5px; }
.q-dense { font-size: 11.5px; line-height: 1.35; }

.quote-mark {
  color: #38bdf8;
  font-size: 16px;
  font-family: Georgia, serif;
  font-weight: 900;
}
.is-thinking .quote-mark { color: #c084fc; }
.is-sc .quote-mark { color: #fbbf24; }

.question-text {
  margin: 0 4px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.topic-footer-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-top: 6px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.thinking-dots-anim, .talking-wave-anim {
  display: flex;
  align-items: center;
  gap: 8px;
}

.think-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #c084fc;
  animation: thinkPulse 1.2s infinite ease-in-out;
}
.td-1 { animation-delay: 0s; }
.td-2 { animation-delay: 0.2s; }
.td-3 { animation-delay: 0.4s; }

@keyframes thinkPulse {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1.3); }
}

.sound-wave-mini {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 12px;
}

.wave-bar {
  width: 2px;
  background: #38bdf8;
  border-radius: 1px;
  animation: wavePulse 0.9s ease-in-out infinite alternate;
}
.is-sc .wave-bar { background: #fbbf24; }
.w-1 { height: 4px; animation-delay: 0.1s; }
.w-2 { height: 9px; animation-delay: 0.3s; }
.w-3 { height: 6px; animation-delay: 0.2s; }
.w-4 { height: 12px; animation-delay: 0.4s; }
.w-5 { height: 8px; animation-delay: 0.15s; }
.w-6 { height: 10px; animation-delay: 0.35s; }
.w-7 { height: 5px; animation-delay: 0.25s; }

@keyframes wavePulse {
  0% { transform: scaleY(0.3); }
  100% { transform: scaleY(1); }
}

.talking-hint {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 500;
}

/* 进退场动画 */
.topic-slide-enter-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.topic-slide-leave-active {
  transition: all 0.3s ease-in;
}
.topic-slide-enter-from {
  opacity: 0;
  transform: translateY(15px) scale(0.96);
}
.topic-slide-leave-to {
  opacity: 0;
  transform: translateY(10px) scale(0.96);
}
</style>
