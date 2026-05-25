"use client";

import { useState, useCallback } from "react";
import ResearchForm from "@/components/ResearchForm";
import AgentSteps from "@/components/AgentSteps";
import ReportView from "@/components/ReportView";
import CostBadge from "@/components/CostBadge";
import { streamResearch, AgentStep, StreamEvent, CostSummary } from "@/lib/stream";

type AppState = "idle" | "running" | "done" | "error";

function getUserId(): string {
  if (typeof window === "undefined") return "anonymous";
  const stored = localStorage.getItem("userId");
  if (stored) return stored;
  const id = "user_" + Math.random().toString(36).slice(2, 9);
  localStorage.setItem("userId", id);
  return id;
}

export default function HomePage() {
  const [appState, setAppState]         = useState<AppState>("idle");
  const [steps, setSteps]               = useState<AgentStep[]>([]);
  const [report, setReport]             = useState("");
  const [costSummary, setCostSummary]   = useState<CostSummary | null>(null);
  const [errorMsg, setErrorMsg]         = useState("");
  const [currentTopic, setCurrentTopic] = useState("");
  const [currentLlm, setCurrentLlm]     = useState<"claude" | "openai">("claude");

  const handleResearch = useCallback((topic: string, llm: "claude" | "openai") => {
    setSteps([]);
    setReport("");
    setCostSummary(null);
    setErrorMsg("");
    setCurrentTopic(topic);
    setCurrentLlm(llm);
    setAppState("running");

    const userId = getUserId();

    streamResearch(
      topic, llm, userId,
      (event: StreamEvent) => {
        if (event.type === "step")   setSteps((p) => [...p, event.data]);
        if (event.type === "report") setReport(event.data.report);
        if (event.type === "cost")   setCostSummary(event.data);
        if (event.type === "done")   setAppState("done");
        if (event.type === "error")  { setErrorMsg(event.data.message); setAppState("error"); }
      },
      (err) => { setErrorMsg(err.message); setAppState("error"); }
    );
  }, []);

  const handleReset = () => {
    setAppState("idle"); setSteps([]); setReport("");
    setCostSummary(null); setErrorMsg(""); setCurrentTopic("");
  };

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "var(--bg)" }}>

      {/* NAV */}
      <nav style={{
        borderBottom: "1px solid var(--border)",
        background: "rgba(15,17,23,0.95)",
        backdropFilter: "blur(12px)",
        position: "sticky", top: 0, zIndex: 50,
      }}>
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div style={{
              width: 32, height: 32, borderRadius: 8,
              background: "linear-gradient(135deg, var(--amber), var(--cyan))",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: "1rem",
            }}>🤖</div>
            <div>
              <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--text)" }}>
                Research Agent
              </div>
              <div style={{ fontSize: "0.7rem", color: "var(--text-3)", fontFamily: "var(--font-mono)" }}>
                LangGraph · DuckDuckGo · Claude / GPT-4o
              </div>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <a
              href="https://github.com/yourusername/agentic-research-assistant"
              target="_blank"
              rel="noopener noreferrer"
              style={{ fontSize: "0.8rem", color: "var(--text-3)", textDecoration: "none" }}
            >
              GitHub ↗
            </a>
            <div style={{
              display: "flex", alignItems: "center", gap: 6,
              fontSize: "0.75rem", color: "var(--green)",
              background: "rgba(74,222,128,0.1)",
              border: "1px solid rgba(74,222,128,0.2)",
              padding: "4px 10px", borderRadius: 20,
            }}>
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--green)", display: "inline-block" }} />
              API Online
            </div>
          </div>
        </div>
      </nav>

      <main className="flex-1 max-w-5xl mx-auto w-full px-4 sm:px-6 py-12">

        {/* HERO */}
        <div style={{ textAlign: "center", marginBottom: "3rem" }}>
          <div style={{
            display: "inline-flex", alignItems: "center", gap: 8,
            background: "rgba(34,211,238,0.08)",
            border: "1px solid rgba(34,211,238,0.2)",
            borderRadius: 20, padding: "5px 14px",
            fontSize: "0.75rem", color: "var(--cyan)",
            fontFamily: "var(--font-mono)", marginBottom: "1.5rem",
            letterSpacing: "0.05em",
          }}>
            ◆ AGENTIC RESEARCH ASSISTANT
          </div>
          <h1 style={{
            fontFamily: "var(--font-display)",
            fontSize: "clamp(2.2rem, 5vw, 3.5rem)",
            fontWeight: 700, lineHeight: 1.15,
            color: "var(--text)", marginBottom: "1rem",
          }}>
            Research any topic.<br />
            <span style={{ color: "var(--amber)", fontStyle: "italic" }}>Autonomously.</span>
          </h1>
          <p style={{
            color: "var(--text-3)", fontSize: "1rem",
            maxWidth: 520, margin: "0 auto", lineHeight: 1.7,
          }}>
            The agent plans sub-questions, searches the web, extracts key facts,
            and writes a cited markdown report — all without your help.
          </p>
        </div>

        {/* FORM */}
        <div style={{
          background: "var(--surface)", border: "1px solid var(--border)",
          borderRadius: 16, padding: "1.5rem", marginBottom: "2rem",
        }}>
          <ResearchForm onSubmit={handleResearch} loading={appState === "running"} />
        </div>

        {/* ERROR */}
        {appState === "error" && (
          <div style={{
            background: "rgba(248,113,113,0.08)", border: "1px solid rgba(248,113,113,0.3)",
            borderRadius: 12, padding: "1.25rem 1.5rem", marginBottom: "1.5rem",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
              <span>⚠️</span>
              <span style={{ color: "var(--red)", fontWeight: 600, fontSize: "0.875rem" }}>Error</span>
            </div>
            <p style={{ color: "#fca5a5", fontSize: "0.875rem", margin: 0 }}>{errorMsg}</p>
            <button
              onClick={handleReset}
              style={{
                marginTop: 12, fontSize: "0.8rem", color: "var(--text-3)",
                background: "var(--surface2)", border: "1px solid var(--border)",
                borderRadius: 8, padding: "6px 14px", cursor: "pointer",
              }}
            >
              ← Try Again
            </button>
          </div>
        )}

        {/* AGENT STEPS */}
        {(steps.length > 0 || appState === "running") && (
          <div style={{ marginBottom: "1.5rem" }}>
            <AgentSteps steps={steps} isRunning={appState === "running"} />
          </div>
        )}

        {/* COST BADGE */}
        {costSummary && (
          <div style={{ marginBottom: "1.5rem" }}>
            <CostBadge cost={costSummary} />
          </div>
        )}

        {/* REPORT */}
        {report && (
          <div style={{ marginBottom: "2rem" }}>
            <ReportView report={report} topic={currentTopic} llm={currentLlm} />
          </div>
        )}

        {/* NEW RESEARCH BUTTON */}
        {appState === "done" && (
          <div style={{ display: "flex", justifyContent: "center", marginBottom: "2rem" }}>
            <button
              onClick={handleReset}
              style={{
                fontFamily: "var(--font-mono)", fontSize: "0.8rem",
                color: "var(--text-3)", background: "var(--surface)",
                border: "1px solid var(--border)", borderRadius: 10,
                padding: "10px 24px", cursor: "pointer",
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
              ← New Research
            </button>
          </div>
        )}

        {/* IDLE STATE */}
        {appState === "idle" && (
          <div style={{
            border: "1px dashed var(--border2)", borderRadius: 16,
            padding: "3rem", textAlign: "center", marginTop: "1rem",
          }}>
            <div style={{ fontSize: "2.5rem", marginBottom: "1rem", opacity: 0.3 }}>⊞</div>
            <p style={{ color: "var(--text-4)", fontSize: "0.875rem", fontFamily: "var(--font-mono)" }}>
              Enter a topic above to start the agent
            </p>
            <div style={{
              display: "flex", justifyContent: "center", gap: "2rem",
              marginTop: "2rem", flexWrap: "wrap",
            }}>
              {[
                { icon: "🔍", label: "Plans sub-questions" },
                { icon: "🌐", label: "Searches the web" },
                { icon: "📄", label: "Extracts key facts" },
                { icon: "✍️", label: "Writes cited report" },
              ].map((step) => (
                <div key={step.label} style={{ textAlign: "center" }}>
                  <div style={{ fontSize: "1.5rem", marginBottom: 6 }}>{step.icon}</div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-4)" }}>{step.label}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* FOOTER */}
      <footer style={{ borderTop: "1px solid var(--border)", padding: "1.25rem 1.5rem" }}>
        <div className="max-w-5xl mx-auto flex justify-between items-center flex-wrap gap-2">
          <span style={{ fontSize: "0.75rem", color: "var(--text-4)" }}>
            Portfolio Project #01 — Agentic Research Assistant
          </span>
          <span style={{ fontSize: "0.75rem", color: "var(--text-4)", fontFamily: "var(--font-mono)" }}>
            LangGraph · DuckDuckGo · Cost-managed
          </span>
        </div>
      </footer>
    </div>
  );
}