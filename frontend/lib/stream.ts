export type AgentStep = {
  type: "plan" | "search" | "read" | "synthesize";
  title: string;
  content: string[];
};

export type CostSummary = {
  total_tokens: number;
  input_tokens: number;
  output_tokens: number;
  estimated_cost_usd: number;
  complexity_tier: "simple" | "complex";
  cache_hit: string | null;
};

export type StreamEvent =
  | { type: "step";   node: string; data: AgentStep }
  | { type: "report"; data: { report: string } }
  | { type: "cost";   data: CostSummary }
  | { type: "done";   data: Record<string, never> }
  | { type: "error";  data: { message: string; limit_type?: string } };

export function streamResearch(
  topic: string,
  llmProvider: "claude" | "openai",
  userId: string,
  onEvent: (event: StreamEvent) => void,
  onError?: (err: Error) => void
): () => void {
  const controller = new AbortController();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  (async () => {
    try {
      const res = await fetch(`${apiUrl}/research/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic,
          llm_provider: llmProvider,
          user_id: userId,
          max_iterations: 1,
        }),
        signal: controller.signal,
      });

      if (!res.ok) throw new Error(`API error ${res.status}`);

      const reader = res.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const raw = line.slice(6).trim();
            if (!raw || raw === "[DONE]") continue;
            try { onEvent(JSON.parse(raw)); } catch { /* skip malformed */ }
          }
        }
      }
    } catch (err: unknown) {
      if ((err as Error).name !== "AbortError") onError?.(err as Error);
    }
  })();

  return () => controller.abort();
}
