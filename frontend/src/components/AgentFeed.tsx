import { useEffect, useRef } from "react";
import type { FeedEvent } from "../lib/ws";

const AGENT_COLOR: Record<string, string> = {
  prospector: "text-agent-prospector",
  bull: "text-agent-bull",
  bear: "text-agent-bear",
  judge: "text-agent-judge",
  outreach: "text-agent-outreach",
  reply: "text-agent-reply",
  closer: "text-agent-closer",
  aftercare: "text-agent-aftercare",
  system: "text-sandstone-500",
  echo: "text-sandstone-400",
};

const ROLE_BG: Record<string, string> = {
  thought: "bg-transparent",
  tool_call: "bg-sandstone-100",
  tool_result: "bg-sandstone-50",
  decision: "bg-terracotta-50",
  message_out: "bg-sandstone-100",
};

const ROLE_ICON: Record<string, string> = {
  thought: "·",
  tool_call: "→",
  tool_result: "←",
  decision: "*",
  message_out: ">",
};

function fmtTs(ts?: number): string {
  if (!ts) return "";
  const d = new Date(ts * 1000);
  return d.toLocaleTimeString("en-GB", { hour12: false });
}

export function AgentFeed({ events }: { events: FeedEvent[] }) {
  const scrollRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [events.length]);

  return (
    <div
      ref={scrollRef}
      className="h-[60vh] overflow-y-auto rounded-lg border border-sandstone-200 bg-sandstone-900 text-sandstone-50 font-mono-feed text-[12.5px] leading-[1.55] p-3"
    >
      {events.length === 0 && (
        <div className="text-sandstone-400 italic">
          Waiting for agents… press <strong>Start Autonomous Run</strong> to begin.
        </div>
      )}
      {events.map((e, i) => {
        const color = AGENT_COLOR[e.agent] || "text-sandstone-300";
        const bg = ROLE_BG[e.role] || "";
        const icon = ROLE_ICON[e.role] || " ";
        return (
          <div key={i} className={`px-2 py-0.5 rounded ${bg} ${bg ? "text-sandstone-900" : ""}`}>
            <span className="text-sandstone-400 mr-2">{fmtTs(e.ts)}</span>
            <span className={`${color} mr-1 font-bold uppercase`}>{e.agent}</span>
            <span className="text-sandstone-400 mr-2">{icon}</span>
            <span className={bg ? "" : "text-sandstone-100"}>{e.content}</span>
          </div>
        );
      })}
    </div>
  );
}
