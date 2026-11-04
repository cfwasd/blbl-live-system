import { ref, onMounted, onUnmounted } from 'vue';

export function useSSE(onEvent: (event: string, data: any) => void) {
  const isConnected = ref(false);
  let eventSource: EventSource | null = null;

  const connect = () => {
    eventSource = new EventSource('/api/stream');
    eventSource.onopen = () => { isConnected.value = true; };
    eventSource.onerror = () => {
      isConnected.value = false;
      eventSource?.close();
      setTimeout(connect, 3000);
    };

    const events = ['danmu', 'super_chat', 'ai_speech', 'stats', 'bgm_action', 'config_sync'];
    events.forEach(evName => {
      eventSource?.addEventListener(evName, (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data);
          onEvent(evName, data);
        } catch (err) {
          console.error(`解析事件 ${evName} 失败`, err);
        }
      });
    });
  };

  onMounted(() => connect());
  onUnmounted(() => eventSource?.close());

  return { isConnected };
}
