"use client";

import { useState } from "react";

interface Props {
  onSubmit: (topic: string, llm: "claude" | "openai") => void;
  loading: boolean;
}

const EXAMPLES = [
  "Impact of large language models on software jobs",
  "How does retrieval-augmented generation work?",
  "Latest advances in quantum computing",
  "Climate change solutions being deployed today",
];

export default function ResearchForm({ onSubmit, loading }: Props) {
  const [topic, setTopic] = useState("");
  const [llm, setLlm] = useState<"claude" | "openai">("claude");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (topic.trim()) onSubmit(topic.trim(), llm);
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* LLM Selector */}
      <div style={{ marginBottom: "1rem" }}>
        <label style={{ fontSize: "0.75rem", color: "var(--text-3)", fontFamily: "var(--font-mono)", letterSpacing: "0.05em", display: "block", marginBottom: 8 }}>
          SELECT MODEL
        </label>
        <div style={{ display: "flex", gap: 8 }}>
          {(["claude", "openai"] as const).map((opt) => (
            <button
              key={opt}
              type="button"
              onClick={() => setLlm(opt)}
              style={{
                padding: "8px 18px", borderRadius: 8, fontSize: "0.82rem",
                fontFamily: "var(--font-mono)", fontWeight: 500,
                cursor: "pointer", transition: "all 0.2s",
                border: llm === opt ? "1px solid var(--amber)" : "1px solid var(--border)",
                background: llm === opt ? "rgba(251,191,36,0.1)" : "var(--surface2)",
                color: llm === opt ? "var(--amber)" : "var(--text-3)",
              }}
            >
              {opt === "claude" ? "🟣 Claude 3.5" : "🟢 GPT-4o"}
            </button>
          ))}
        </div>
      </div>

      {/* Topic Input */}
      <div style={{ marginBottom: "1rem" }}>
        <label style={{ fontSize: "0.75rem", color: "var(--text-3)", fontFamily: "var(--font-mono)", letterSpacing: "0.05em", display: "block", marginBottom: 8 }}>
          RESEARCH TOPIC
        </label>
        <div style={{ position: "relative" }}>
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g. How does RAG improve LLM accuracy?"
            disabled={loading}
            style={{
              width: "100%", padding: "12px 150px 12px 16px",
              background: "var(--surface2)",
              border: "1px solid var(--border)",
              borderRadius: 10, fontSize: "0.9rem",
              color: "var(--text)", outline: "none",
              transition: "border-color 0.2s",
              fontFamily: "var(--font-sans)",
            }}
            onFocus={(e) => (e.currentTarget.style.borderColor = "var(--cyan)")}
            onBlur={(e) => (e.currentTarget.style.borderColor = "var(--border)")}
          />
          <button
            type="submit"
            disabled={loading || !topic.trim()}
            style={{
              position: "absolute", right: 6, top: "50%", transform: "translateY(-50%)",
              padding: "8px 18px", borderRadius: 8,
              background: loading || !topic.trim() ? "var(--border)" : "var(--amber)",
              color: loading || !topic.trim() ? "var(--text-4)" : "#000",
              border: "none", cursor: loading || !topic.trim() ? "not-allowed" : "pointer",
              fontWeight: 600, fontSize: "0.82rem", transition: "all 0.2s",
              display: "flex", alignItems: "center", gap: 6,
            }}
          >
            {loading ? (
              <>
                <span style={{
                  width: 12, height: 12,
                  border: "2px solid #000", borderTopColor: "transparent",
                  borderRadius: "50%", display: "inline-block",
                  animation: "researchSpin 0.8s linear infinite",
                }} />
                Running
              </>
            ) : "Research →"}
          </button>
        </div>
      </div>

      {/* Examples */}
      {!loading && (
        <div>
          <span style={{ fontSize: "0.72rem", color: "var(--text-4)", fontFamily: "var(--font-mono)" }}>
            EXAMPLES:
          </span>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 6 }}>
            {EXAMPLES.map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setTopic(t)}
                style={{
                  fontSize: "0.75rem", padding: "4px 10px",
                  background: "var(--surface2)",
                  border: "1px solid var(--border)",
                  borderRadius: 6, color: "var(--text-3)",
                  cursor: "pointer", transition: "all 0.2s",
                  fontFamily: "var(--font-sans)",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = "var(--cyan)";
                  e.currentTarget.style.color = "var(--cyan)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = "var(--border)";
                  e.currentTarget.style.color = "var(--text-3)";
                }}
              >
                {t.length > 42 ? t.slice(0, 42) + "…" : t}
              </button>
            ))}
          </div>
        </div>
      )}

      <style>{`
        @keyframes researchSpin { to { transform: rotate(360deg); } }
      `}</style>
    </form>
  );
}