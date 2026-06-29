# Cortex: An Autonomous Agent That Thinks, Acts, and Remembers

A production-ready, modular autonomous agent system built in Python.  
Plans tasks, selects tools, executes steps, self-corrects, and maintains persistent memory. All driven by any OpenAI-compatible LLM.

---

## Architecture

```
Cortex/
├── app/
│   ├── agent/
│   │   ├── core.py          # Orchestrator — full cognitive loop
│   │   ├── planner.py       # Goal → sub-task decomposition
│   │   ├── executor.py      # Sub-task execution engine
│   │   ├── reflector.py     # Self-critique + final synthesis
│   │   ├── memory.py        # Unified memory interface
│   │   └── tools_router.py  # Dynamic tool selection + dispatch
│   ├── tools/
│   │   ├── code_runner.py   # Python execution sandbox (subprocess)
│   │   ├── web_search.py    # Tavily / SerpAPI / mock fallback
│   │   ├── file_system.py   # Safe file I/O (workspace-scoped)
│   │   └── api_client.py    # Generic HTTP client
│   ├── memory/
│   │   ├── vector_store.py  # FAISS semantic memory (persistent)
│   │   └── episodic_store.py# JSON task history
│   ├── llm/
│   │   ├── client.py        # OpenAI-compatible LLM wrapper
│   │   └── prompts.py       # System prompts for each component
│   ├── utils/
│   │   ├── config.py        # .env-driven settings
│   │   └── logger.py        # Rich-formatted logging
│   └── main.py              # FastAPI server
├── tests/                   # pytest test suite
├── examples/                # Sample tasks
├── run.py                   # CLI launcher
├── requirements.txt
└── .env.example
```

## Cognitive Loop

```
User Goal
   │
   ▼
[Planner] ──── LLM + Memory ────► Structured Plan (N sub-tasks)
   │
   ▼
[Executor] (per sub-task)
   ├── Tool Router → selects best tool
   ├── Strategy Generator → LLM generates content/code
   └── Tool Execution → code_runner / web_search / file_system / api_client
   │
   ▼
[Reflector] (per sub-task)
   └── Evaluates result → triggers retry if needed
   │
   ▼
[Reflector] (final)
   └── Synthesizes all results → Final Output
   │
   ▼
[Memory Update]
   ├── Vector store (semantic recall)
   └── Episodic store (task history)
```

---

## Quickstart

### 1. Install

```bash
git clone https://github.com/your-username/agent-os
cd agent-os
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env — set OPENAI_API_KEY (or any compatible provider)
```

Compatible with:
- **OpenAI** (`gpt-4o`, `gpt-4o-mini`)
- **Together AI** (`meta-llama/…`)
- **Groq** (`llama3-…`)
- **Ollama** (set `LLM_BASE_URL=http://localhost:11434/v1`, `OPENAI_API_KEY=ollama`)

### 3. Run

```bash
# Single task (CLI)
python run.py -t "Write a Python function to detect palindromes and test it"

# Interactive multi-task loop
python run.py -i

# REST API server
python run.py --api
# → Docs at http://localhost:8000/docs
```

---

## API Usage

```bash
# Run a task
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"goal": "Explain quicksort with a Python implementation"}'

# Stream progress (SSE)
curl -N http://localhost:8000/stream \
  -H "Content-Type: application/json" \
  -d '{"goal": "Research FAISS and write a similarity search demo"}'

# Memory stats
curl http://localhost:8000/memory/stats
```

---

## Testing

```bash
pytest tests/ -v
```

The test suite covers:
- Planner decomposition and fallback behaviour
- Reflector evaluation + graceful error handling
- Agent memory (working, context, recall)
- Code runner (success, failure, syntax check)
- File system (read/write, workspace escape prevention)
- Tools router (hint bypass, execution dispatch)
- API client (localhost blocking)

---

## Extending the System

### Add a new tool

1. Create `app/tools/my_tool.py` with a `run(...)` method
2. Register it in `app/agent/tools_router.py` → `TOOL_REGISTRY`
3. Add its description to `TOOLS_ROUTER_SYSTEM` in `app/llm/prompts.py`
4. Handle it in `tools_router.execute_tool()`

### Swap the LLM

Change `LLM_BASE_URL` and `LLM_MODEL` in `.env`. No code changes required.

### Use a different embedding model

Change `EMBEDDING_MODEL` in `.env`. Any `sentence-transformers` model works; update `EMBEDDING_DIM` in `vector_store.py` if it differs from 384.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | required | API key for your LLM provider |
| `LLM_BASE_URL` | `https://api.openai.com/v1` | Any OpenAI-compatible endpoint |
| `LLM_MODEL` | `gpt-4o-mini` | Model name |
| `LLM_TEMPERATURE` | `0.3` | LLM sampling temperature |
| `MAX_ITERATIONS` | `10` | Max sub-tasks per run |
| `MAX_RETRIES` | `3` | Retries per failed sub-task |
| `TAVILY_API_KEY` | optional | For real web search |
| `SERPAPI_KEY` | optional | Alternative search backend |
| `API_PORT` | `8000` | FastAPI server port |

---

## License

MIT
