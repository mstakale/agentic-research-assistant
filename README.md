# 🤖 Agentic Research Assistant

> **An autonomous AI agent that researches any topic end-to-end — plans, searches, reads, and writes a cited report without human intervention.**

![Tech Stack](https://img.shields.io/badge/LangGraph-Agent_Framework-blue?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat-square)
![Next.js](https://img.shields.io/badge/Next.js_14-Frontend-black?style=flat-square)
![Python](https://img.shields.io/badge/Python_3.11-Language-3776AB?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-Containerised-2496ED?style=flat-square)

---

## 🎯 What This Project Demonstrates

This project goes beyond a simple chatbot. It shows how to build a **production-aware agentic system** — where an LLM doesn't just answer a question but autonomously executes a multi-step research workflow, manages its own decisions, and streams live progress to a user interface.

| Skill Area | What's Demonstrated |
|---|---|
| **Agentic AI** | LangGraph state machine with conditional loops |
| **RAG Architecture** | Search → Extract → Synthesize pipeline |
| **LLM Engineering** | Switchable Claude / GPT-4o with model routing |
| **Cost Management** | Token counting, semantic caching, budget guards |
| **Backend** | FastAPI with Server-Sent Events (SSE) streaming |
| **Frontend** | Real-time Next.js UI with live agent step visualization |
| **DevOps** | Fully Dockerised, single command to run |

---

## 🚀 Run Locally

> See [Quick Start](#-quick-start) below — runs fully locally with Docker in one command.

**Example queries to try:**
- *"How does retrieval-augmented generation work?"*
- *"Compare LangChain vs LlamaIndex for production RAG"*
- *"Latest advances in quantum computing 2025"*

---

## 🏗️ Architecture

The core insight: **the agent doesn't wait for you**. It breaks the problem down, executes each step autonomously, and streams live progress back to the UI — so you watch it think in real time.

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface                        │
│         Next.js · Real-time SSE streaming               │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP POST + SSE stream
┌─────────────────────▼───────────────────────────────────┐
│                   FastAPI Backend                        │
│     Budget Guard → Cache Check → Agent Runner           │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│              LangGraph Agent (4 nodes)                   │
│                                                          │
│  ① PLAN          Break topic into 4 sub-questions        │
│       │                                                  │
│  ② SEARCH        DuckDuckGo search per sub-question      │
│       │                                                  │
│  ③ READ          LLM extracts 3 key facts per result     │
│       │                                                  │
│  ④ [enough?] ──No──→ loop back to ② SEARCH              │
│       │Yes                                               │
│  ⑤ SYNTHESIZE    Assemble cited markdown report          │
└─────────────────────────────────────────────────────────┘
```

### Why LangGraph?

Most tutorials use simple LLM chains. LangGraph enables **stateful agent loops** — the agent can evaluate its own progress and decide to search again if it hasn't gathered enough information. This is how real production agents work at companies like Perplexity and You.com.

---

## 💰 Cost Management (Production Feature)

One of the most overlooked aspects of LLM applications is **cost control**. This project implements four layers:

### 1. Model Routing
Not every query needs an expensive model. A lightweight classifier routes:
- Simple queries (e.g. "what is X") → **Claude Haiku / GPT-4o-mini** (~$0.001)
- Complex queries (compare, analyse, recent) → **Claude Sonnet / GPT-4o** (~$0.05)

### 2. Two-Level Semantic Cache
```
Request → Exact hash match? → Return cached ($0.00)
        → Similar query (92% cosine similarity)? → Return cached ($0.00)
        → No match → Run agent → Store in cache
```

### 3. Per-User Budget Guards
- Daily token limit per user
- Daily cost limit per user  
- Global cost ceiling
- Hard abort if limits exceeded — checked *before* any LLM call

### 4. Token Counting & Cost Transparency
Every response includes exact token usage and estimated cost — shown live in the UI.

**Real impact:** The same query costs **$0.18 unoptimised → $0.03 with routing → $0.00 on cache hit.**

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| **Python 3.11** | Core language |
| **FastAPI** | REST API + SSE streaming endpoint |
| **LangGraph** | Stateful agent graph with conditional routing |
| **LangChain** | LLM abstraction layer |
| **Claude 3.5 Sonnet / Haiku** | Anthropic LLMs |
| **GPT-4o / GPT-4o-mini** | OpenAI LLMs |
| **DuckDuckGo Search** | Free web search (no API key) |
| **Redis** | Semantic cache + budget tracking |

### Frontend
| Technology | Purpose |
|---|---|
| **Next.js 14** | React framework (App Router) |
| **TypeScript** | Type safety |
| **Tailwind CSS** | Styling |
| **react-markdown** | Markdown report rendering |
| **SSE Client** | Real-time agent step streaming |

### Infrastructure
| Technology | Purpose |
|---|---|
| **Docker + Docker Compose** | One-command local setup |
| **Railway** | Backend deployment |
| **Vercel** | Frontend deployment |

---

## 📁 Project Structure

```
agentic-research-assistant/
│
├── backend/
│   ├── agent/
│   │   ├── graph.py        # LangGraph StateGraph definition
│   │   ├── nodes.py        # Plan, Search, Read, Synthesize nodes
│   │   └── state.py        # Typed state schema (ResearchState)
│   │
│   ├── api/
│   │   └── main.py         # FastAPI app + /research/stream endpoint
│   │
│   ├── utils/
│   │   ├── llm.py          # LLM factory (Claude / OpenAI switcher)
│   │   ├── router.py       # Model complexity classifier
│   │   ├── cache.py        # Two-level Redis semantic cache
│   │   ├── budget.py       # Per-user budget guard
│   │   └── token_counter.py # Token usage + cost calculator
│   │
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx        # Main research UI
│   │   └── globals.css     # Theme + markdown styles
│   │
│   ├── components/
│   │   ├── ResearchForm.tsx  # Topic input + model selector
│   │   ├── AgentSteps.tsx    # Live step visualization
│   │   ├── ReportView.tsx    # Markdown report + download
│   │   └── CostBadge.tsx     # Token usage + cost display
│   │
│   ├── lib/
│   │   └── stream.ts       # SSE client utility
│   │
│   └── Dockerfile
│
├── docker-compose.yml      # Wires backend + frontend + Redis
└── README.md
```

---

## ⚡ Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running
- API keys for [Anthropic](https://console.anthropic.com) and/or [OpenAI](https://platform.openai.com)

### 1. Clone the repo
```bash
git clone https://github.com/YOURUSERNAME/agentic-research-assistant.git
cd agentic-research-assistant
```

### 2. Add your API keys
```bash
cp backend/.env.example backend/.env
```
Open `backend/.env` and fill in:
```env
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

### 3. Run with Docker
```bash
docker-compose up --build
```

### 4. Open the app
| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |

That's it. No Python setup, no Node setup, no Redis setup — Docker handles everything.

---

## 🔌 API Reference

### `POST /research/stream`
Streams agent progress as Server-Sent Events.

**Request:**
```json
{
  "topic": "How does RAG improve LLM accuracy?",
  "llm_provider": "claude",
  "user_id": "user_abc123",
  "max_iterations": 1
}
```

**SSE Event types:**
```
{ "type": "step",   "data": { "title": "Research Plan", "content": [...] } }
{ "type": "report", "data": { "report": "# Report\n..." } }
{ "type": "cost",   "data": { "total_tokens": 1842, "estimated_cost_usd": 0.00921 } }
{ "type": "done",   "data": {} }
{ "type": "error",  "data": { "message": "..." } }
```

### `GET /usage/{user_id}`
Returns today's token and cost usage for a user.

```json
{
  "tokens_used": 4821,
  "tokens_limit": 100000,
  "cost_usd": 0.024,
  "cost_limit_usd": 1.00,
  "requests_today": 3
}
```

---

## 🧠 Key Engineering Decisions

**Why SSE instead of WebSockets?**
SSE is simpler, unidirectional (server → client), and works over standard HTTP — no special infrastructure needed. Perfect for streaming agent progress.

**Why LangGraph instead of simple chains?**
LangGraph enables conditional routing — the agent can loop back and search again if it hasn't gathered enough facts. Simple chains can't do this.

**Why DuckDuckGo instead of Tavily?**
DuckDuckGo is completely free with no API key required — lowers the barrier to run this project. In production, Bing Search API or Tavily would provide higher quality results.

**Why Redis for both cache and budget?**
Both features need fast key lookups with TTL (time-to-live). Redis handles both elegantly with built-in expiry — no separate database needed.

---

## 🗺️ Roadmap

- [ ] Add authentication (NextAuth.js)
- [ ] Export reports as PDF
- [ ] Support uploading documents as additional context
- [ ] Add evaluation metrics (RAGAS faithfulness score)
- [ ] Multi-language report generation
- [ ] Slack / email report delivery

---

## 📄 License

MIT — feel free to use this as a starting point for your own projects.

---

## 👤 Author

Built by **Manisha Takale** as part of an AI/RAG engineering portfolio.

- GitHub: [@mstakale](https://github.com/mstakale)
- LinkedIn: [Manisha Takale](https://www.linkedin.com/in/manisha-takale-29a17914/)

---

*If this project was useful or interesting, consider giving it a ⭐*
