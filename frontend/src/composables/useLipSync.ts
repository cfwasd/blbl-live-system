import { ref } from 'vue';

export function useLipSync() {
  let audioCtx: AudioContext | null = null;
  let analyser: AnalyserNode | null = null;
  const currentAmplitude = ref(0);

  const initAudio = () => {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
    }
    if (audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
  };

  const playBase64Audio = async (
    base64Audio: string,
    onProgress?: (progress: number) => void,
    onStart?: () => void,
    onEnded?: () => void
  ) => {
    initAudio();
    if (!audioCtx || !analyser) return;

    try {
      const base64Data = base64Audio.replace(/^data:audio\/\w+;base64,/, '');
      const binary = atob(base64Data);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
      }

      const audioBuffer = await audioCtx.decodeAudioData(bytes.buffer);
      const source = audioCtx.createBufferSource();
      source.buffer = audioBuffer;

      source.connect(analyser);
      analyser.connect(audioCtx.destination);

      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      let isPlaying = true;
      let startTime = 0;

      const updateLoop = () => {
        if (!isPlaying || !analyser || !audioCtx) return;
        analyser.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i];
        }
        const avg = sum / dataArray.length;
        currentAmplitude.value = Math.min(1.0, avg / 60);

        // 实时打字机同步进度 (0.0 ~ 1.0)
        if (onProgress && audioBuffer.duration > 0) {
          const elapsed = audioCtx.currentTime - startTime;
          const progress = Math.min(1.0, Math.max(0, elapsed / audioBuffer.duration));
          onProgress(progress);
        }

        requestAnimationFrame(updateLoop);
      };

      source.onended = () => {
        isPlaying = false;
        currentAmplitude.value = 0;
        if (onProgress) onProgress(1.0);
        if (onEnded) onEnded();
      };

      // 音频真正起播第一毫秒：触发 onStart 保证字体与声音同频起播
      startTime = audioCtx.currentTime;
      if (onStart) onStart();
      source.start(0);
      requestAnimationFrame(updateLoop);
    } catch (e) {
      console.warn('音频解码或播放失败', e);
      if (onEnded) onEnded();
    }
  };

  const resumeAudio = () => {
    initAudio();
  };

  return { currentAmplitude, playBase64Audio, resumeAudio };
}
