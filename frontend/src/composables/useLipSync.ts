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

  const playBase64Audio = async (base64Audio: string, onEnded?: () => void) => {
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

      const updateLoop = () => {
        if (!isPlaying || !analyser) return;
        analyser.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i];
        }
        const avg = sum / dataArray.length;
        currentAmplitude.value = Math.min(1.0, avg / 60);
        requestAnimationFrame(updateLoop);
      };

      source.onended = () => {
        isPlaying = false;
        currentAmplitude.value = 0;
        if (onEnded) onEnded();
      };

      source.start(0);
      requestAnimationFrame(updateLoop);
    } catch (e) {
      console.warn('音频解码或播放失败', e);
      if (onEnded) onEnded();
    }
  };

  return { currentAmplitude, playBase64Audio };
}
