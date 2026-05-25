"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Props {
  report: string;
  topic: string;
  llm: string;
}

export default function ReportView({ report, topic, llm }: Props) {
  const handleCopy = () => navigator.clipboard.writeText(report);

  const handleDownload = () => {
    const blob = new Blob([report], { type: "text/markdown" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = `research-${topic.slice(0, 30).replace(/\s+/g, "-").toLowerCase()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{
      background: "var(--surface)",
      border: "1px solid var(--border)",
      borderRadius: 12, overflow: "hidden",
    }}>
      {/* Header */}
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "12px 16px",
        borderBottom: "1px solid var(--border)",
        background: "var(--surface2)",
        flexWrap: "wrap", gap: 8,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: "1rem" }}>📄</span>
          <span style={{ fontWeight: 600, fontSize: "0.875rem", color: "var(--text)" }}>
            Research Report
          </span>
          <span style={{
            fontSize: "0.7rem", fontFamily: "var(--font-mono)",
            padding: "3px 8px", borderRadius: 6,
            background: llm === "claude" ? "rgba(251,191,36,0.1)" : "rgba(74,222,128,0.1)",
            border: `1px solid ${llm === "claude" ? "rgba(251,191,36,0.3)" : "rgba(74,222,128,0.3)"}`,
            color: llm === "claude" ? "var(--amber)" : "var(--green)",
          }}>
            {llm === "claude" ? "Claude 3.5" : "GPT-4o"}
          </span>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={handleCopy} style={{
            fontSize: "0.75rem", padding: "6px 12px",
            background: "var(--surface)", border: "1px solid var(--border)",
            borderRadius: 7, color: "var(--text-3)", cursor: "pointer",
            transition: "all 0.2s",
          }}
          onMouseEnter={e => (e.currentTarget.style.borderColor = "var(--cyan)")}
          onMouseLeave={e => (e.currentTarget.style.borderColor = "var(--border)")}>
            Copy
          </button>
          <button onClick={handleDownload} style={{
            fontSize: "0.75rem", padding: "6px 12px",
            background: "var(--amber)", border: "none",
            borderRadius: 7, color: "#000", cursor: "pointer",
            fontWeight: 600, transition: "opacity 0.2s",
          }}
          onMouseEnter={e => (e.currentTarget.style.opacity = "0.85")}
          onMouseLeave={e => (e.currentTarget.style.opacity = "1")}>
            ↓ Download .md
          </button>
        </div>
      </div>

      {/* Body */}
      <div style={{ padding: "2rem", maxHeight: "70vh", overflowY: "auto" }}>
        <div className="report-content">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{report}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}