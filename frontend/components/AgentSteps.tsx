"use client";

import { AgentStep } from "@/lib/stream";

const STEP_CONFIG: Record<string, { icon: string; color: string; bg: string }> = {
  plan:      { icon: "◆", color: "#22d3ee", bg: "rgba(34,211,238,0.08)" },
  search:    { icon: "⌖", color: "#fbbf24", bg: "rgba(251,191,36,0.08)" },
  read:      { icon: "⊞", color: "#c084fc", bg: "rgba(192,132,252,0.08)" },
  synthesize:{ icon: "◈", color: "#4ade80", bg: "rgba(74,222,128,0.08)"  },
};

interface Props {
  steps: AgentStep[];
  isRunning: boolean;
}

export default function AgentSteps({ steps, isRunning }: Props) {
  if (steps.length === 0 && !isRunning) return null;

  return (
    <div style={{
      background: "var(--surface)",
      border: "1px solid var(--border)",
      borderRadius: 12,
      overflow: "hidden",
    }}>
      {/* Header */}
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "12px 16px",
        borderBottom: "1px solid var(--border)",
        background: "var(--surface2)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{ display: "flex", gap: 5 }}>
            {["#ef4444","#f59e0b","#22c55e"].map(c => (
              <div key={c} style={{ width: 10, height: 10, borderRadius: "50%", background: c, opacity: 0.6 }} />
            ))}
          </div>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--text-3)", letterSpacing: "0.05em" }}>
            AGENT ACTIVITY
          </span>
        </div>
        {isRunning && (
          <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "0.72rem", color: "var(--green)" }}>
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--green)", display: "inline-block", animation: "blink 1s step-end infinite" }} />
            RUNNING
          </div>
        )}
      </div>

      {/* Steps */}
      <div style={{ padding: "1rem", display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        {steps.map((step, i) => {
          const cfg = STEP_CONFIG[step.type] ?? { icon: "·", color: "var(--text-3)", bg: "var(--surface2)" };
          return (
            <div key={i} style={{
              background: cfg.bg,
              border: `1px solid ${cfg.color}30`,
              borderRadius: 10, padding: "0.75rem 1rem",
              animation: `fadeUp 0.4s ${i * 0.05}s both`,
            }}>
              {/* Step header */}
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                <span style={{ color: cfg.color, fontSize: "0.9rem" }}>{cfg.icon}</span>
                <span style={{
                  fontFamily: "var(--font-mono)", fontSize: "0.72rem",
                  color: cfg.color, letterSpacing: "0.08em", textTransform: "uppercase", fontWeight: 600,
                }}>
                  {step.title}
                </span>
              </div>
              {/* Step content */}
              <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                {Array.isArray(step.content) && step.content.map((line, j) => (
                  typeof line === "string" && (
                    <div key={j} style={{
                      display: "flex", alignItems: "flex-start", gap: 6,
                      fontSize: "0.8rem", color: "var(--text-3)", lineHeight: 1.5,
                    }}>
                      <span style={{ color: cfg.color, marginTop: 1, flexShrink: 0 }}>›</span>
                      <span>{line}</span>
                    </div>
                  )
                ))}
              </div>
            </div>
          );
        })}

        {/* Running indicator */}
        {isRunning && (
          <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "0.5rem 0" }}>
            <div style={{ display: "flex", gap: 4 }}>
              {[0,1,2].map(i => (
                <div key={i} style={{
                  width: 6, height: 6, borderRadius: "50%",
                  background: "var(--amber)",
                  animation: `blink 1.2s ${i * 0.2}s ease-in-out infinite`,
                }} />
              ))}
            </div>
            <span style={{ fontSize: "0.8rem", color: "var(--text-3)" }}>Processing...</span>
          </div>
        )}
      </div>
    </div>
  );
}