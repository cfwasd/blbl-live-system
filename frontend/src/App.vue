<template>
  <div class="overlay-screen" :class="'theme-' + currentTheme" @click="handleScreenClick">
    <!-- 场景 A：温馨二次元卧室/书房深夜治愈舞台 (非透明模式呈现) -->
    <div v-if="currentTheme === 'cozy_room'" class="ambient-cozy-space">
      <!-- 1. 温馨夜空星月书房大窗景 -->
      <div class="cozy-window-frame">
        <div class="window-sky">
          <div class="moon-crescent"></div>
          <div class="window-stars">
            <span v-for="n in 14" :key="n" :class="'w-star ws-' + n">✦</span>
          </div>
        </div>
        <div class="window-mullion-v"></div>
        <div class="window-mullion-h"></div>
        <div class="curtain-drape curtain-l"></div>
        <div class="curtain-drape curtain-r"></div>
      </div>

      <!-- 2. 暖光台灯与漫反射环境氛围光晕 -->
      <div class="warm-glow glow-mascot-desk"></div>
      <div class="warm-glow glow-chat-ambient"></div>
      <div class="warm-glow glow-room-ceiling"></div>

      <!-- 3. 书房温馨书架与暖木装饰剪影 -->
      <div class="cozy-study-decor">
        <div class="decor-desk-shelf"></div>
        <div class="decor-warm-lamp">
          <div class="lamp-shade"></div>
          <div class="lamp-beam"></div>
        </div>
      </div>

      <!-- 4. 深夜治愈电台高质感标牌 -->
      <div class="studio-watermark cozy-theme-wm">
        <div class="wm-badge cozy-badge">
          <span class="wm-pulse cozy-pulse"></span>
          <span class="wm-tag">LATE NIGHT ON AIR</span>
        </div>
        <div class="wm-main">
          <span class="wm-icon">✦</span>
          <span class="wm-text">SHIZUKU COZY STUDY</span>
          <span class="wm-icon">✦</span>
        </div>
        <span class="wm-sub">BILIBILI VIRTUAL LIVE · HEALING RADIO</span>
      </div>

      <!-- 5. 飘浮漫舞的暖金萤火与微光粒子 (24颗温暖光尘) -->
      <div class="warm-dust-particles">
        <span v-for="n in 24" :key="n" :class="'warm-particle wp-' + n"></span>
      </div>
    </div>

    <!-- 场景 B：赛博电竞深海舞台布景 -->
    <div v-else-if="currentTheme === 'deep_sea'" class="ambient-cyber-space">
      <!-- 1. 背景多层梦幻霓虹极光与光斑 -->
      <div class="nebula-glow glow-left-chat"></div>
      <div class="nebula-glow glow-right-mascot"></div>
      <div class="nebula-glow glow-center-top"></div>

      <!-- 2. 3D 透视赛博地平线网格地台 (空间纵深感) -->
      <div class="cyber-grid-floor"></div>
      <div class="cyber-horizon-line"></div>

      <!-- 3. 背景科技电竞动态音频频谱装饰墙 -->
      <div class="cyber-wall-spectrum">
        <span v-for="i in 18" :key="i" class="spec-bar" :class="'sb-' + (i % 6 + 1)"></span>
      </div>

      <!-- 4. 背景高科技全息直播间标牌 -->
      <div class="studio-watermark">
        <div class="wm-badge">
          <span class="wm-pulse"></span>
          <span class="wm-tag">LIVE ON AIR</span>
        </div>
        <div class="wm-main">
          <span class="wm-icon">✦</span>
          <span class="wm-text">GEMINI CYBER STUDIO</span>
          <span class="wm-icon">✦</span>
        </div>
        <span class="wm-sub">BILIBILI VIRTUAL LIVE · AI PRO ENGINE</span>
      </div>

      <!-- 5. 飘浮闪烁四角星芒 -->
      <div class="ambient-stars">
        <span class="star s-1">✦</span>
        <span class="star s-2">★</span>
        <span class="star s-3">✦</span>
        <span class="star s-4">★</span>
        <span class="star s-5">✦</span>
      </div>

      <!-- 6. 全息极细霓虹框与四角科技角标 -->
      <div class="holo-frame">
        <div class="frame-bracket bracket-tl"></div>
        <div class="frame-bracket bracket-tr"></div>
        <div class="frame-bracket bracket-bl"></div>
        <div class="frame-bracket bracket-br"></div>
      </div>

      <!-- 7. 飘动星尘光粒群 (24颗晶莹星尘微光) -->
      <div class="dust-particles">
        <span v-for="n in 24" :key="n" :class="'particle p-' + n"></span>
      </div>
    </div>

    <!-- 全局音频解锁浮层 (若浏览器或OBS策略阻止静音自动播放) -->
    <transition name="pill-fade">
      <div v-if="audioNeedsUnlock" class="audio-unlock-pill" @click.stop="unlockAudio">
        <span class="unlock-icon">🎵</span>
        <span class="unlock-text">点击任意处开启直播伴奏与语音播报</span>
        <span class="unlock-pulse"></span>
      </div>
    </transition>

    <!-- 新观众入场萌系猫耳迎宾横幅 -->
    <StreamWelcomeBanner ref="welcomeRef" />

    <!-- 顶部居中 SuperChat 醒目打赏区 -->
    <SuperChat ref="scRef" />

    <!-- 顶部四角独立锚定导航区 (不会挤压底部舞台) -->
    <div class="dock-top-left">
      <AuroraPlayer
        ref="bgmRef"
        :isDucking="isSpeaking"
        @autoplayBlocked="audioNeedsUnlock = true"
        @playStarted="audioNeedsUnlock = false"
        @timeUpdate="bgmCurrentTime = $event"
      />
    </div>

    <div class="dock-top-center">
      <LiveClock :roomId="currentRoomId" />
      <StreamMarquee :text="marqueeText" />
    </div>

    <div class="dock-top-right">
      <DataHUD :stats="globalStats" />
      <StreamGoalBar :currentCount="globalStats.danmu_count" :targetCount="100" />
    </div>

    <!-- 中部偏下：伴奏实时滚动歌词 + 观众互动玩法指南卡 -->
    <div class="dock-center-widgets">
      <StreamLyrics
        :trackId="currentBgmTrack?.id"
        :trackTitle="currentBgmTrack?.title"
        :currentTime="bgmCurrentTime"
      />
      <StreamCommandGuide :items="guideItems" />
    </div>

    <!-- 左侧互动区域：弹幕墙 + 其正上方的“正在回复中/思考中”专栏卡片 -->
    <div class="dock-left-chat-zone">
      <!-- 提问与回复专栏卡片 (弹幕墙正上方升起，视角焦点自然协调) -->
      <div class="topic-banner-wrapper">
        <CurrentTopic
          :active="isSpeaking || isThinking"
          :isThinking="isThinking"
          :isSpeaking="isSpeaking"
          :topic="currentTopic"
        />
      </div>

      <!-- 实时弹幕墙 -->
      <DanmuList ref="danmuListRef" />
    </div>

    <!-- 右侧舞台区：立绘与全息舞台地台 + 旁边的心率情绪仪 -->
    <div class="dock-right-mascot-zone">
      <div class="mascot-side-widget">
        <StreamEmotionHeartbeat
          :isSpeaking="isSpeaking"
          :isThinking="isThinking"
          :expression="currentExpression"
          :motion="currentMotion"
        />
      </div>

      <Live2DStage
        :mouthOpenY="currentAmplitude"
        :scale="mascotScale"
        :isSpeaking="isSpeaking"
        :speechText="currentSpeechText"
        :motion="currentMotion"
        :expression="currentExpression"
        :showStagePedestal="currentTheme !== 'transparent'"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useSSE } from './composables/useSSE';
import { useLipSync } from './composables/useLipSync';
import Live2DStage from './components/Live2DStage.vue';
import DanmuList from './components/DanmuList.vue';
import DataHUD from './components/DataHUD.vue';
import AuroraPlayer from './components/AuroraPlayer.vue';
import SuperChat from './components/SuperChat.vue';
import LiveClock from './components/LiveClock.vue';
import CurrentTopic, { TopicData } from './components/CurrentTopic.vue';
import StreamGoalBar from './components/StreamGoalBar.vue';
import StreamMarquee from './components/StreamMarquee.vue';
import StreamCommandGuide from './components/StreamCommandGuide.vue';
import StreamEmotionHeartbeat from './components/StreamEmotionHeartbeat.vue';
import StreamWelcomeBanner from './components/StreamWelcomeBanner.vue';
import StreamLyrics from './components/StreamLyrics.vue';

const THEMES = ['cozy_room', 'transparent', 'deep_sea'];
const currentTheme = ref('cozy_room');
const mascotScale = ref(1.0);
const currentRoomId = ref<number | string>('');

// 大屏可自定义文案
const marqueeText = ref('');
const guideItems = ref<any[]>([]);

// 伴奏实时歌词驱动
const bgmCurrentTime = ref(0);
const welcomeRef = ref<any>(null);

// 互动状态：思考与说话
const isThinking = ref(false);
const isSpeaking = ref(false);

const currentSpeechText = ref('');
const currentMotion = ref('');
const currentExpression = ref('');
const currentTopic = ref<TopicData | null>(null);

const audioNeedsUnlock = ref(false);

const scRef = ref<any>(null);
const bgmRef = ref<any>(null);
const danmuListRef = ref<any>(null);

const currentBgmTrack = computed(() => bgmRef.value?.currentTrack || null);

const globalStats = ref({
  total_tokens: 0,
  danmu_count: 0,
  ai_reply_count: 0,
  blocked_count: 0,
  top_users: []
});

const { currentAmplitude, playBase64Audio, resumeAudio } = useLipSync();

// 一键解锁全局音频
const unlockAudio = () => {
  audioNeedsUnlock.value = false;
  resumeAudio();
  if (bgmRef.value) {
    bgmRef.value.tryPlay();
  }
};

const handleScreenClick = () => {
  if (audioNeedsUnlock.value) {
    unlockAudio();
  }
};

// 键盘快捷键监听 (T 切换场景风格, M 切换伴奏, 任意按键尝试解锁音频)
const handleKeydown = (e: KeyboardEvent) => {
  if (audioNeedsUnlock.value) {
    unlockAudio();
  }
  if (e.key === 't' || e.key === 'T') {
    const curIdx = THEMES.indexOf(currentTheme.value);
    const nextIdx = (curIdx + 1) % THEMES.length;
    currentTheme.value = THEMES[nextIdx];
  } else if (e.key === 'm' || e.key === 'M') {
    bgmRef.value?.playNextTrack(true);
  }
};

onMounted(async () => {
  window.addEventListener('keydown', handleKeydown);

  // 初次挂载时主动拉取已保存的后台配置，防止刷新丢失舞台与风格设置
  try {
    const res = await fetch('/api/config');
    if (res.ok) {
      const data = await res.json();
      if (data.mascot) {
        if (typeof data.mascot.scale === 'number') {
          mascotScale.value = data.mascot.scale;
        }
        if (data.mascot.theme) {
          currentTheme.value = data.mascot.theme;
        }
      }
      if (data.bilibili?.room_id) {
        currentRoomId.value = data.bilibili.room_id;
      }
      if (data.broadcast) {
        if (data.broadcast.marquee_text) marqueeText.value = data.broadcast.marquee_text;
        if (data.broadcast.guide_items) guideItems.value = data.broadcast.guide_items;
      }
    }
  } catch (err) {
    console.warn('拉取初始配置异常:', err);
  }
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown);
});

// SSE 实时事件分发
useSSE((eventName: string, data: any) => {
  if (eventName === 'danmu') {
    danmuListRef.value?.addDanmu(data);
  } else if (eventName === 'viewer_welcome') {
    welcomeRef.value?.addWelcome(data);
  } else if (eventName === 'super_chat') {
    scRef.value?.addSC(data);
    danmuListRef.value?.addDanmu({
      id: data.id,
      uname: data.uname,
      content: `[SC ￥${data.price}] ${data.content}`,
      badge: '醒目留言',
      level: 20
    });
  } else if (eventName === 'stats') {
    globalStats.value = data;
  } else if (eventName === 'bgm_action') {
    if (data.action === 'play_song' && data.song) {
      bgmRef.value?.playSong(data.song, data.uname);
    } else if (data.action === 'request_failed') {
      bgmRef.value?.showFailedNotification(data.message || '点歌未成功');
    } else if (data.action === 'switch' || data.action === 'next' || data.action === 'random') {
      bgmRef.value?.playNextTrack(false, true, data.uname);
    } else if (data.action === 'request') {
      bgmRef.value?.requestSong(data.payload, data.uname);
    } else if (data.action === 'pause') {
      bgmRef.value?.setPlayState(false);
    } else if (data.action === 'play') {
      bgmRef.value?.setPlayState(true);
    }
  } else if (eventName === 'config_sync') {
    if (data.theme) {
      if (data.theme === 'toggle') {
        const curIdx = THEMES.indexOf(currentTheme.value);
        const nextIdx = (curIdx + 1) % THEMES.length;
        currentTheme.value = THEMES[nextIdx];
      } else {
        currentTheme.value = data.theme;
      }
    }
    if (data.mascot?.scale) {
      mascotScale.value = data.mascot.scale;
    }
    if (data.broadcast) {
      if (data.broadcast.marquee_text) marqueeText.value = data.broadcast.marquee_text;
      if (data.broadcast.guide_items) guideItems.value = data.broadcast.guide_items;
    }
  } else if (eventName === 'ai_thinking') {
    // 零延迟即刻响应：观众弹幕触发 AI 后立刻弹出思考状态卡片与动效
    isThinking.value = true;
    currentTopic.value = data;
    currentMotion.value = 'Think';
    currentExpression.value = 'think';
  } else if (eventName === 'ai_speech') {
    currentMotion.value = data.motion || 'Wave';
    currentExpression.value = data.expression || 'smile';

    const fullText = data.text || '';

    if (data.audio) {
      // 初始重置字幕文本为空
      currentSpeechText.value = '';

      playBase64Audio(
        data.audio,
        // onProgress: 实时打字机同步，紧随音频播放进度逐字同频浮现！
        (progress: number) => {
          const totalChars = fullText.length;
          const count = Math.min(totalChars, Math.floor(progress * totalChars) + 1);
          currentSpeechText.value = fullText.slice(0, count);
        },
        // onStart: 音频发声第一毫秒
        () => {
          isThinking.value = false;
          isSpeaking.value = true;
          currentSpeechText.value = fullText.slice(0, 1);
          currentTopic.value = data.reply_to || currentTopic.value;
        },
        // onEnded: 音频播报结束
        () => {
          currentSpeechText.value = fullText;
          isSpeaking.value = false;
          setTimeout(() => {
            if (!isSpeaking.value) {
              currentSpeechText.value = '';
            }
          }, 2000);
        }
      );
    } else {
      // 无音频兜底模式：打字机以 70ms 间隔平滑逐字推进
      isThinking.value = false;
      isSpeaking.value = true;
      currentSpeechText.value = '';
      currentTopic.value = data.reply_to || currentTopic.value;

      let charIdx = 0;
      const typeTimer = setInterval(() => {
        charIdx++;
        currentSpeechText.value = fullText.slice(0, charIdx);
        if (charIdx >= fullText.length) {
          clearInterval(typeTimer);
          setTimeout(() => {
            isSpeaking.value = false;
            currentSpeechText.value = '';
          }, 3000);
        }
      }, 70);
    }
  }
});
</script>

<style>
* {
  box-sizing: border-box;
}

body, html {
  margin: 0;
  padding: 0;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background: transparent !important;
  user-select: none;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

.overlay-screen {
  width: 100vw;
  height: 100vh;
  position: relative;
  overflow: hidden;
  transition: background 0.5s ease;
}

/* 场景模式 */
.theme-transparent {
  background: transparent !important;
}

.theme-deep_sea {
  background: radial-gradient(circle at 80% 80%, rgba(99, 102, 241, 0.4) 0%, rgba(30, 27, 75, 0.85) 40%, #090e24 75%, #030712 100%);
}

.theme-cozy_room {
  background: radial-gradient(circle at 75% 70%, rgba(245, 158, 11, 0.28) 0%, rgba(120, 53, 15, 0.45) 35%, #19120c 70%, #0a0604 100%);
}

/* ================= 场景 A：温馨二次元卧室/书房环境装饰 ================= */
.ambient-cozy-space {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
  overflow: hidden;
}

/* 1. 书房拱形深夜星月大窗景 */
.cozy-window-frame {
  position: absolute;
  top: 40px;
  right: max(60px, 6vw);
  width: 440px;
  height: 520px;
  border-radius: 220px 220px 14px 14px;
  border: 4px solid rgba(180, 83, 9, 0.45);
  box-shadow: 0 0 50px rgba(245, 158, 11, 0.15), inset 0 0 40px rgba(10, 15, 30, 0.9);
  overflow: hidden;
  background: #060914;
  z-index: 1;
}

.window-sky {
  position: absolute;
  width: 100%;
  height: 100%;
  background: linear-gradient(180deg, #050713 0%, #0c1427 55%, #172554 100%);
}

.moon-crescent {
  position: absolute;
  top: 45px;
  right: 55px;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  box-shadow: 7px 7px 0 0 #fde68a;
  filter: drop-shadow(0 0 16px rgba(253, 230, 138, 0.85));
  animation: moonGlowPulse 4s ease-in-out infinite alternate;
}

@keyframes moonGlowPulse {
  0% { filter: drop-shadow(0 0 12px rgba(253, 230, 138, 0.7)); }
  100% { filter: drop-shadow(0 0 22px rgba(253, 230, 138, 0.95)); }
}

.window-stars {
  position: absolute;
  width: 100%;
  height: 100%;
}

.w-star {
  position: absolute;
  color: #fef08a;
  font-size: 10px;
  animation: starTwinkle 3s ease-in-out infinite alternate;
  text-shadow: 0 0 6px rgba(254, 240, 138, 0.8);
}
.ws-1 { top: 18%; left: 22%; animation-delay: 0.2s; font-size: 12px; }
.ws-2 { top: 28%; left: 45%; animation-delay: 1.1s; font-size: 8px; }
.ws-3 { top: 15%; left: 75%; animation-delay: 1.8s; font-size: 11px; }
.ws-4 { top: 38%; left: 18%; animation-delay: 0.6s; font-size: 9px; }
.ws-5 { top: 48%; left: 35%; animation-delay: 2.3s; font-size: 13px; color: #fde047; }
.ws-6 { top: 32%; left: 62%; animation-delay: 0.9s; font-size: 7px; }
.ws-7 { top: 60%; left: 24%; animation-delay: 1.4s; font-size: 10px; }
.ws-8 { top: 52%; left: 78%; animation-delay: 2.0s; font-size: 8px; }
.ws-9 { top: 72%; left: 42%; animation-delay: 0.4s; font-size: 11px; }
.ws-10 { top: 68%; left: 68%; animation-delay: 1.6s; font-size: 9px; }
.ws-11 { top: 82%; left: 30%; animation-delay: 2.5s; font-size: 7px; }
.ws-12 { top: 22%; left: 52%; animation-delay: 0.8s; font-size: 10px; }
.ws-13 { top: 88%; left: 72%; animation-delay: 1.3s; font-size: 8px; }
.ws-14 { top: 42%; left: 85%; animation-delay: 2.1s; font-size: 10px; }

.window-mullion-v {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 3.5px;
  height: 100%;
  background: rgba(180, 83, 9, 0.45);
  box-shadow: 0 0 4px rgba(0, 0, 0, 0.5);
}

.window-mullion-h {
  position: absolute;
  top: 55%;
  left: 0;
  width: 100%;
  height: 3.5px;
  background: rgba(180, 83, 9, 0.45);
  box-shadow: 0 0 4px rgba(0, 0, 0, 0.5);
}

.curtain-drape {
  position: absolute;
  top: 0;
  width: 65px;
  height: 100%;
  pointer-events: none;
}
.curtain-l {
  left: 0;
  background: linear-gradient(90deg, rgba(146, 64, 14, 0.7) 0%, rgba(180, 83, 9, 0.3) 60%, transparent 100%);
  border-right: 1px dashed rgba(245, 158, 11, 0.2);
}
.curtain-r {
  right: 0;
  background: linear-gradient(-90deg, rgba(146, 64, 14, 0.7) 0%, rgba(180, 83, 9, 0.3) 60%, transparent 100%);
  border-left: 1px dashed rgba(245, 158, 11, 0.2);
}

/* 2. 暖光漫反射环境光晕 */
.warm-glow {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
}
.glow-mascot-desk {
  bottom: 0%;
  right: 5%;
  width: 650px;
  height: 550px;
  background: radial-gradient(ellipse, rgba(245, 158, 11, 0.38) 0%, rgba(217, 119, 6, 0.16) 50%, transparent 80%);
  filter: blur(80px);
}
.glow-chat-ambient {
  bottom: 8%;
  left: 5%;
  width: 560px;
  height: 420px;
  background: radial-gradient(ellipse, rgba(251, 191, 36, 0.22) 0%, rgba(180, 83, 9, 0.1) 60%, transparent 80%);
  filter: blur(80px);
}
.glow-room-ceiling {
  top: 0%;
  left: 30%;
  width: 750px;
  height: 260px;
  background: radial-gradient(ellipse, rgba(253, 230, 138, 0.16) 0%, transparent 70%);
  filter: blur(75px);
}

/* 3. 书房温馨木质书桌与暖光台灯装饰 */
.cozy-study-decor {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 580px;
  height: 85px;
  pointer-events: none;
  z-index: 2;
}
.decor-desk-shelf {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 100%;
  height: 70px;
  background: linear-gradient(180deg, rgba(120, 53, 15, 0.45) 0%, rgba(35, 18, 9, 0.95) 100%);
  border-top: 2px solid rgba(245, 158, 11, 0.35);
  border-radius: 24px 0 0 0;
  box-shadow: 0 -10px 30px rgba(0, 0, 0, 0.6);
}

/* 4. 深夜治愈书房标牌 */
.cozy-theme-wm {
  color: #fbbf24 !important;
  border-color: rgba(245, 158, 11, 0.45) !important;
  background: rgba(30, 18, 11, 0.65) !important;
  box-shadow: 0 0 25px rgba(245, 158, 11, 0.15) !important;
  opacity: 0.45 !important;
}
.cozy-badge {
  background: rgba(245, 158, 11, 0.2) !important;
  border-color: rgba(245, 158, 11, 0.5) !important;
}
.cozy-pulse {
  background: #fbbf24 !important;
  box-shadow: 0 0 8px #f59e0b !important;
}

/* 5. 飘浮漫舞的暖金萤火与微光粒子 */
.warm-dust-particles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 3;
  overflow: hidden;
}
.warm-particle {
  position: absolute;
  border-radius: 50%;
  background: radial-gradient(circle, #fde047 0%, rgba(245, 158, 11, 0.6) 50%, transparent 70%);
  opacity: 0.6;
  animation: floatWarmEmber 10s infinite ease-in-out;
}
.wp-1 { width: 5px; height: 5px; top: 20%; left: 22%; animation-duration: 9s; }
.wp-2 { width: 8px; height: 8px; top: 40%; left: 35%; animation-duration: 12s; animation-delay: 1.5s; }
.wp-3 { width: 4px; height: 4px; top: 65%; left: 16%; animation-duration: 8s; animation-delay: 2.5s; }
.wp-4 { width: 6px; height: 6px; top: 25%; left: 60%; animation-duration: 14s; }
.wp-5 { width: 7px; height: 7px; top: 58%; left: 55%; animation-duration: 11s; animation-delay: 1s; }
.wp-6 { width: 5px; height: 5px; top: 75%; left: 42%; animation-duration: 13s; }
.wp-7 { width: 4px; height: 4px; top: 30%; left: 80%; animation-duration: 10s; animation-delay: 2s; }
.wp-8 { width: 7px; height: 7px; top: 50%; left: 75%; animation-duration: 11s; }
.wp-9 { width: 4px; height: 4px; top: 15%; left: 45%; animation-duration: 15s; }
.wp-10 { width: 6px; height: 6px; top: 80%; left: 25%; animation-duration: 12s; }
.wp-11 { width: 3px; height: 3px; top: 45%; left: 10%; animation-duration: 9s; }
.wp-12 { width: 7px; height: 7px; top: 70%; left: 85%; animation-duration: 12s; }
.wp-13 { width: 5px; height: 5px; top: 18%; left: 88%; animation-duration: 13s; }
.wp-14 { width: 6px; height: 6px; top: 86%; left: 65%; animation-duration: 10s; }
.wp-15 { width: 8px; height: 8px; top: 35%; left: 50%; animation-duration: 14s; animation-delay: 1s; }
.wp-16 { width: 4px; height: 4px; top: 58%; left: 30%; animation-duration: 11s; }
.wp-17 { width: 3px; height: 3px; top: 82%; left: 50%; animation-duration: 8s; }
.wp-18 { width: 5px; height: 5px; top: 12%; left: 72%; animation-duration: 12s; }
.wp-19 { width: 4px; height: 4px; top: 62%; left: 88%; animation-duration: 10s; }
.wp-20 { width: 7px; height: 7px; top: 48%; left: 95%; animation-duration: 13s; }
.wp-21 { width: 4px; height: 4px; top: 78%; left: 68%; animation-duration: 11s; }
.wp-22 { width: 5px; height: 5px; top: 28%; left: 18%; animation-duration: 14s; }
.wp-23 { width: 3px; height: 3px; top: 90%; left: 38%; animation-duration: 9s; }
.wp-24 { width: 6px; height: 6px; top: 8%; left: 62%; animation-duration: 12s; }

@keyframes floatWarmEmber {
  0%, 100% { transform: translateY(0) scale(0.9); opacity: 0.35; }
  50% { transform: translateY(-26px) scale(1.35); opacity: 0.95; }
}

/* 舞台地台在温馨书房风格下的暖金渲染 */
.theme-cozy_room .pedestal-outer-ring {
  border: 1px solid rgba(245, 158, 11, 0.45) !important;
  box-shadow: 0 0 25px rgba(245, 158, 11, 0.3) !important;
}
.theme-cozy_room .pedestal-inner-ring {
  border: 1px dashed rgba(251, 191, 36, 0.6) !important;
  box-shadow: 0 0 16px rgba(251, 191, 36, 0.45) !important;
}
.theme-cozy_room .pedestal-core-glow {
  background: radial-gradient(ellipse at center, rgba(245, 158, 11, 0.35) 0%, transparent 70%) !important;
}
.theme-cozy_room .pedestal-light-cone {
  background: linear-gradient(to top, rgba(245, 158, 11, 0.16) 0%, transparent 100%) !important;
}

/* 沉浸式赛博电竞房与深海背景装饰 */
.ambient-cyber-space {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
  overflow: hidden;
}

/* 梦幻星云光斑 */
.nebula-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  pointer-events: none;
}
.glow-left-chat {
  bottom: 10%;
  left: 5%;
  width: 550px;
  height: 400px;
  background: radial-gradient(ellipse, rgba(14, 165, 233, 0.35) 0%, rgba(59, 130, 246, 0.12) 60%, transparent 80%);
}
.glow-right-mascot {
  bottom: 0%;
  right: 5%;
  width: 650px;
  height: 550px;
  background: radial-gradient(ellipse, rgba(168, 85, 247, 0.45) 0%, rgba(236, 72, 153, 0.2) 50%, transparent 80%);
}
.glow-center-top {
  top: 0%;
  left: 30%;
  width: 750px;
  height: 280px;
  background: radial-gradient(ellipse, rgba(99, 102, 241, 0.3) 0%, transparent 70%);
}

/* 3D 透视赛博地平线网格地台 (空间纵深感) */
.cyber-grid-floor {
  position: absolute;
  bottom: 0;
  left: -20%;
  width: 140%;
  height: 380px;
  background-image:
    linear-gradient(to right, rgba(56, 189, 248, 0.3) 1.5px, transparent 1.5px),
    linear-gradient(to bottom, rgba(192, 132, 252, 0.3) 1.5px, transparent 1.5px);
  background-size: 80px 40px;
  transform: perspective(350px) rotateX(68deg);
  transform-origin: bottom center;
  mask-image: linear-gradient(to top, rgba(0,0,0,1) 20%, rgba(0,0,0,0.6) 70%, transparent 100%);
  -webkit-mask-image: linear-gradient(to top, rgba(0,0,0,1) 20%, rgba(0,0,0,0.6) 70%, transparent 100%);
  pointer-events: none;
}

/* 发光地平线 */
.cyber-horizon-line {
  position: absolute;
  bottom: 120px;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent 5%, rgba(56, 189, 248, 0.4) 25%, rgba(192, 132, 252, 0.8) 50%, rgba(56, 189, 248, 0.4) 75%, transparent 95%);
  box-shadow: 0 0 16px rgba(56, 189, 248, 0.7);
  pointer-events: none;
}

/* 背景科技电竞动态音频频谱装饰墙 */
.cyber-wall-spectrum {
  position: absolute;
  top: 42%;
  left: 42%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  gap: 8px;
  opacity: 0.26;
  pointer-events: none;
}
.spec-bar {
  width: 5px;
  background: linear-gradient(to top, #38bdf8, #c084fc);
  border-radius: 4px;
  animation: wallSpecAnim 1.6s ease-in-out infinite alternate;
}
.sb-1 { height: 25px; animation-delay: 0.1s; }
.sb-2 { height: 45px; animation-delay: 0.3s; }
.sb-3 { height: 35px; animation-delay: 0.2s; }
.sb-4 { height: 60px; animation-delay: 0.4s; }
.sb-5 { height: 40px; animation-delay: 0.15s; }
.sb-6 { height: 50px; animation-delay: 0.35s; }

@keyframes wallSpecAnim {
  0% { transform: scaleY(0.4); opacity: 0.3; }
  100% { transform: scaleY(1.1); opacity: 0.9; }
}

/* 高科技全息直播间背景标牌 */
.studio-watermark {
  position: absolute;
  top: 50%;
  left: 42%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  opacity: 0.35;
  color: #38bdf8;
  letter-spacing: 3px;
  font-family: monospace;
  pointer-events: none;
  user-select: none;
}
.wm-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 2px 10px;
  border-radius: 12px;
  background: rgba(56, 189, 248, 0.15);
  border: 1px solid rgba(56, 189, 248, 0.35);
}
.wm-pulse {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #38bdf8;
  box-shadow: 0 0 8px #38bdf8;
}
.wm-tag { font-size: 10px; font-weight: 800; color: #38bdf8; letter-spacing: 2px; }
.wm-main { display: flex; align-items: center; gap: 8px; }
.wm-icon { font-size: 16px; color: #c084fc; text-shadow: 0 0 10px #c084fc; }
.wm-text { font-size: 20px; font-weight: 900; color: #f1f5f9; text-shadow: 0 0 15px rgba(56, 189, 248, 0.6); }
.wm-sub { font-size: 10px; letter-spacing: 5px; color: #94a3b8; }

/* 飘浮闪烁四角星芒 */
.ambient-stars {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
.star {
  position: absolute;
  color: #38bdf8;
  font-size: 14px;
  animation: starTwinkle 3s ease-in-out infinite alternate;
  text-shadow: 0 0 10px rgba(56, 189, 248, 0.8);
}
.s-1 { top: 22%; left: 35%; animation-delay: 0.5s; color: #c084fc; font-size: 16px; }
.s-2 { top: 35%; left: 25%; animation-delay: 1.2s; color: #38bdf8; font-size: 11px; }
.s-3 { top: 28%; left: 58%; animation-delay: 2.1s; color: #fbbf24; font-size: 14px; }
.s-4 { top: 65%; left: 45%; animation-delay: 0.8s; color: #f472b6; font-size: 13px; }
.s-5 { top: 18%; left: 70%; animation-delay: 1.7s; color: #38bdf8; font-size: 15px; }

@keyframes starTwinkle {
  0% { opacity: 0.2; transform: scale(0.8) rotate(0deg); }
  50% { opacity: 0.9; transform: scale(1.3) rotate(45deg); }
  100% { opacity: 0.3; transform: scale(0.9) rotate(90deg); }
}

/* 全息 Neon 边框与科技角标 */
.holo-frame {
  position: absolute;
  top: 12px;
  left: 12px;
  right: 12px;
  bottom: 12px;
  border: 1px solid rgba(56, 189, 248, 0.2);
  box-shadow: inset 0 0 30px rgba(56, 189, 248, 0.05);
  pointer-events: none;
  z-index: 5;
}
.frame-bracket {
  position: absolute;
  width: 18px;
  height: 18px;
  border-color: rgba(56, 189, 248, 0.8);
}
.bracket-tl { top: -2px; left: -2px; border-top: 2.5px solid; border-left: 2.5px solid; }
.bracket-tr { top: -2px; right: -2px; border-top: 2.5px solid; border-right: 2.5px solid; }
.bracket-bl { bottom: -2px; left: -2px; border-bottom: 2.5px solid; border-left: 2.5px solid; }
.bracket-br { bottom: -2px; right: -2px; border-bottom: 2.5px solid; border-right: 2.5px solid; }

/* 飘动星尘光粒 */
.dust-particles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 2;
  overflow: hidden;
}
.particle {
  position: absolute;
  border-radius: 50%;
  background: radial-gradient(circle, #38bdf8 0%, rgba(56, 189, 248, 0) 70%);
  opacity: 0.55;
  animation: floatDust 12s infinite ease-in-out;
}
.p-1 { width: 4px; height: 4px; top: 15%; left: 18%; animation-duration: 9s; }
.p-2 { width: 7px; height: 7px; top: 38%; left: 32%; animation-duration: 13s; animation-delay: 2s; background: radial-gradient(circle, #c084fc 0%, transparent 70%); }
.p-3 { width: 3px; height: 3px; top: 68%; left: 12%; animation-duration: 8s; animation-delay: 3s; }
.p-4 { width: 5px; height: 5px; top: 22%; left: 58%; animation-duration: 15s; }
.p-5 { width: 6px; height: 6px; top: 62%; left: 52%; animation-duration: 11s; animation-delay: 1s; background: radial-gradient(circle, #f472b6 0%, transparent 70%); }
.p-6 { width: 5px; height: 5px; top: 78%; left: 38%; animation-duration: 14s; }
.p-7 { width: 4px; height: 4px; top: 28%; left: 78%; animation-duration: 12s; animation-delay: 2.5s; }
.p-8 { width: 6px; height: 6px; top: 48%; left: 72%; animation-duration: 11s; }
.p-9 { width: 4px; height: 4px; top: 12%; left: 42%; animation-duration: 16s; }
.p-10 { width: 5px; height: 5px; top: 82%; left: 22%; animation-duration: 13s; }
.p-11 { width: 3px; height: 3px; top: 42%; left: 8%; animation-duration: 10s; }
.p-12 { width: 6px; height: 6px; top: 72%; left: 82%; animation-duration: 12s; background: radial-gradient(circle, #fbbf24 0%, transparent 70%); }
.p-13 { width: 4px; height: 4px; top: 18%; left: 88%; animation-duration: 14s; }
.p-14 { width: 5px; height: 5px; top: 88%; left: 62%; animation-duration: 10s; }
.p-15 { width: 7px; height: 7px; top: 32%; left: 48%; animation-duration: 15s; animation-delay: 1.5s; background: radial-gradient(circle, #38bdf8 0%, transparent 70%); }
.p-16 { width: 4px; height: 4px; top: 55%; left: 28%; animation-duration: 12s; }
.p-17 { width: 3px; height: 3px; top: 85%; left: 48%; animation-duration: 9s; }
.p-18 { width: 5px; height: 5px; top: 15%; left: 75%; animation-duration: 13s; }
.p-19 { width: 4px; height: 4px; top: 60%; left: 85%; animation-duration: 11s; }
.p-20 { width: 6px; height: 6px; top: 45%; left: 92%; animation-duration: 14s; }
.p-21 { width: 4px; height: 4px; top: 76%; left: 65%; animation-duration: 12s; }
.p-22 { width: 5px; height: 5px; top: 25%; left: 20%; animation-duration: 15s; }
.p-23 { width: 3px; height: 3px; top: 92%; left: 35%; animation-duration: 10s; }
.p-24 { width: 6px; height: 6px; top: 10%; left: 60%; animation-duration: 13s; }

@keyframes floatDust {
  0%, 100% { transform: translateY(0) scale(0.85); opacity: 0.3; }
  50% { transform: translateY(-30px) scale(1.3); opacity: 0.95; }
}

/* 全局音频解锁药丸 */
.audio-unlock-pill {
  position: absolute;
  top: 90px;
  left: 50%;
  transform: translateX(-50%);
  background: linear-gradient(135deg, #0284c7 0%, #6366f1 100%);
  color: #fff;
  border-radius: 30px;
  padding: 8px 22px;
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  box-shadow: 0 8px 25px rgba(2, 132, 199, 0.5), 0 0 15px rgba(99, 102, 241, 0.4);
  z-index: 100;
  animation: unlockPillBounce 2s infinite ease-in-out;
}
@keyframes unlockPillBounce {
  0%, 100% { transform: translateX(-50%) translateY(0); }
  50% { transform: translateX(-50%) translateY(-6px); }
}
.unlock-icon { font-size: 15px; }
.unlock-pulse {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #38bdf8;
  box-shadow: 0 0 10px #38bdf8;
  animation: pulse 1s infinite;
}

.pill-fade-enter-active, .pill-fade-leave-active {
  transition: all 0.3s ease;
}
.pill-fade-enter-from, .pill-fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-10px);
}

/* 锚定布局：四角精准独立定位，永不挤压越界 */
.dock-top-left {
  position: absolute;
  top: 24px;
  left: 28px;
  z-index: 30;
}

.dock-top-center {
  position: absolute;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 30;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.dock-top-right {
  position: absolute;
  top: 20px;
  right: 28px;
  z-index: 30;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* 中部偏下：伴奏实时歌词 + 互动指令卡 */
.dock-center-widgets {
  position: absolute;
  bottom: 24px;
  left: 530px;
  z-index: 25;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 左侧交互区：弹幕墙与正上方的专栏卡片 */
.dock-left-chat-zone {
  position: absolute;
  bottom: 24px;
  left: 28px;
  z-index: 25;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.topic-banner-wrapper {
  min-height: 40px;
  display: flex;
  align-items: flex-end;
}

/* 右侧偏中立绘舞台区 (向中间靠拢，避开右上角贡献榜/HUD遮挡) */
.dock-right-mascot-zone {
  position: absolute;
  bottom: 0px;
  right: max(180px, 16vw);
  z-index: 20;
  display: flex;
  align-items: flex-end;
  gap: 16px;
}
.mascot-side-widget {
  margin-bottom: 50px;
}
</style>
