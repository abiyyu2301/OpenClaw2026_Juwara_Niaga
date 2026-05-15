/** WebSocket client for the live agent feed. */

export interface FeedEvent {
  agent: string;
  role: string;
  content: string;
  lead_id?: number | null;
  ts?: number;
}

export function connectRun(
  runId: number,
  onEvent: (e: FeedEvent) => void,
  onStatus?: (open: boolean) => void,
): WebSocket {
  // Vite proxy: /ws -> ws://localhost:8000
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  const url = `${proto}//${location.host}/ws/runs/${runId}`;
  const ws = new WebSocket(url);
  ws.onopen = () => onStatus?.(true);
  ws.onclose = () => onStatus?.(false);
  ws.onerror = () => onStatus?.(false);
  ws.onmessage = (msg) => {
    try {
      onEvent(JSON.parse(msg.data));
    } catch {
      // ignore non-JSON frames
    }
  };
  return ws;
}
