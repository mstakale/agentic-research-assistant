"use client";

import { CostSummary } from "@/lib/stream";

export default function CostBadge({ cost }: { cost: CostSummary }) {
  const isFree     = cost.cache_hit !== null;
  const costColor  = isFree ? "var(--green)"
    : cost.estimated_cost_usd < 0.01 ? "var(--cyan)"
    : cost.estimated_cost_usd < 0.05 ? "var(--amber)"
    : "var(--red)";

  return (
    <div style={{
      display: "flex", flexWrap: "wrap", alignItems: "center", gap: 12,
      padding: "10px 16px",
      background: "var(--surface)",
      border: "1px solid var(--border)",
      borderRadius: 10,
      fontFamily: "var(--font-mono)", fontSize: "0.78rem",
    }}>
      {/* Cost */}
      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <span style={{ color: "var(--text-4)" }}>COST</span>
        <span style={{ color: costColor, fontWeight: 700 }}>
          {isFree ? "$0.00" : `$${cost.estimated_cost_usd.toFixed(5)}`}
        </span>
        {isFree && (
          <span style={{
            fontSize: "0.65rem", padding: "2px 6px", borderRadius: 4,
            background: "rgba(74,222,128,0.1)",
            border: "1px solid rgba(74,222,128,0.2)",
            color: "var(--green)",
          }}>cached</span>
        )}
      </div>

      <span style={{ color: "var(--border2)" }}>|</span>

      {/* Tokens */}
      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <span style={{ color: "var(--text-4)" }}>TOKENS</span>
        <span style={{ color: "var(--text-2)", fontWeight: 600 }}>
          {cost.total_tokens.toLocaleString()}
        </span>
        <span style={{ color: "var(--text-4)", fontSize: "0.7rem" }}>
          ({cost.input_tokens?.toLocaleString() ?? 0} in / {cost.output_tokens?.toLocaleString() ?? 0} out)
        </span>
      </div>

      <span style={{ color: "var(--border2)" }}>|</span>

      {/* Model tier */}
      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <span style={{ color: "var(--text-4)" }}>TIER</span>
        <span style={{
          padding: "2px 8px", borderRadius: 4, fontSize: "0.7rem",
          fontWeight: 600, textTransform: "uppercase",
          background: cost.complexity_tier === "simple"
            ? "rgba(74,222,128,0.1)" : "rgba(251,191,36,0.1)",
          border: `1px solid ${cost.complexity_tier === "simple"
            ? "rgba(74,222,128,0.3)" : "rgba(251,191,36,0.3)"}`,
          color: cost.complexity_tier === "simple" ? "var(--green)" : "var(--amber)",
        }}>
          {cost.complexity_tier}
        </span>
      </div>

      {/* Cache hit detail */}
      {cost.cache_hit && (
        <>
          <span style={{ color: "var(--border2)" }}>|</span>
          <div style={{ display: "flex", alignItems: "center", gap: 5, color: "var(--green)" }}>
            <span>✓</span>
            <span>
              {cost.cache_hit.startsWith("semantic")
                ? `Semantic match (${cost.cache_hit.split(":")[1]} similarity)`
                : "Exact cache hit"}
            </span>
          </div>
        </>
      )}
    </div>
  );
}