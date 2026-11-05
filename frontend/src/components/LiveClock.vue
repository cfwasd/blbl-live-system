<template>
  <div class="live-clock-card">
    <div class="clock-left">
      <div class="live-status-pill">
        <span class="live-indicator-dot"></span>
        <span class="live-text">LIVE</span>
      </div>
      <div class="room-id-tag">
        <span class="bili-tv-icon">📺</span>
        <span class="room-num">{{ roomId ? '房号 ' + roomId : 'B站直连' }}</span>
      </div>
    </div>

    <div class="clock-divider"></div>

    <div class="clock-right">
      <div class="time-display">
        <span class="time-hhmm">{{ timeHours }}:{{ timeMinutes }}</span>
        <span class="time-ss">:{{ timeSeconds }}</span>
      </div>
      <div class="date-display">
        <span class="date-text">{{ dateString }}</span>
        <span class="weekday-text">{{ weekdayString }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';

defineProps<{
  roomId?: number | string;
}>();

const timeHours = ref('00');
const timeMinutes = ref('00');
const timeSeconds = ref('00');
const dateString = ref('');
const weekdayString = ref('');

const WEEKDAYS = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'];

const updateTime = () => {
  const now = new Date();
  timeHours.value = String(now.getHours()).padStart(2, '0');
  timeMinutes.value = String(now.getMinutes()).padStart(2, '0');
  timeSeconds.value = String(now.getSeconds()).padStart(2, '0');

  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  dateString.value = `${year}.${month}.${day}`;
  weekdayString.value = WEEKDAYS[now.getDay()];
};

let timer: any = null;

onMounted(() => {
  updateTime();
  timer = setInterval(updateTime, 1000);
});

onUnmounted(() => {
  if (timer) clearInterval(timer);
});
</script>

<style scoped>
.live-clock-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(11, 15, 25, 0.82);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(56, 189, 248, 0.25);
  border-radius: 40px;
  padding: 8px 18px 8px 14px;
  color: #fff;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45), inset 0 0 10px rgba(56, 189, 248, 0.08);
  user-select: none;
}

.clock-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.live-status-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: rgba(239, 68, 68, 0.18);
  border: 1px solid rgba(239, 68, 68, 0.45);
  padding: 2px 7px;
  border-radius: 10px;
}

.live-indicator-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #ef4444;
  box-shadow: 0 0 8px #ef4444;
  animation: liveBlink 1.4s infinite;
}

@keyframes liveBlink {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.3; transform: scale(0.8); }
}

.live-text {
  font-size: 10px;
  font-weight: 900;
  color: #fca5a5;
  letter-spacing: 0.5px;
}

.room-id-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  color: #94a3b8;
  font-weight: 600;
}
.bili-tv-icon {
  font-size: 11px;
}
.room-num {
  font-family: monospace;
}

.clock-divider {
  width: 1px;
  height: 28px;
  background: rgba(255, 255, 255, 0.12);
}

.clock-right {
  display: flex;
  flex-direction: column;
}

.time-display {
  display: flex;
  align-items: baseline;
  line-height: 1.1;
}

.time-hhmm {
  font-family: monospace;
  font-size: 18px;
  font-weight: 800;
  color: #f1f5f9;
  letter-spacing: 0.5px;
}

.time-ss {
  font-family: monospace;
  font-size: 13px;
  font-weight: 700;
  color: #38bdf8;
  margin-left: 1px;
}

.date-display {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  color: #94a3b8;
  font-weight: 600;
  margin-top: 2px;
}

.weekday-text {
  color: #c084fc;
}
</style>
