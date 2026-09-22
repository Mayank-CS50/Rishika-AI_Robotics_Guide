# Rishika Backend — Voice AI Agent Service

The Python backend for **Rishika (Voice AI LFR Teaching Assistant)**. Built on [LiveKit Agents](https://docs.livekit.io/agents), it orchestrates a real-time conversational pipeline using **Deepgram Nova-3** (STT), **Google Gemini** (LLM & Tool Orchestrator), and **Murf Falcon** (TTS).

---

## 🛠️ Architecture Overview

```
User Audio Stream
      │
      ▼
[Deepgram Nova-3 STT] (language="multi")
      │
      ▼
[Google Gemini 3.5 Flash] (LLM + Function Tool Calling)
      ├── SQLite Storage (Profiles, Escalations, Calls)
      ├── Interactive Card Dispatch (LiveKit Data Channel)
      └── Specialist Agent Routing (Kabir PID Coach)
      │
      ▼
[Murf Falcon TTS] (Voice: Anisha / Samar)
      │
      ▼
Synthesized Audio Stream
```

---

## 📦 Key Backend Modules

| Module | Location | Purpose |
| :--- | :--- | :--- |
| **Main Pipeline** | [`src/agent.py`](src/agent.py) | Entrypoint connecting STT, LLM, TTS, LiveKit session, and function tools |
| **Analytics Engine** | [`src/analytics.py`](src/analytics.py) | Call outcome classification, KPI tracking, and terminal stats |
| **Database & Memory** | [`src/db_memory.py`](src/db_memory.py) | SQLite student profile store with explicit consent gates |
| **Educational Tools** | [`src/educational_tools.py`](src/educational_tools.py) | Free Dictionary API, Open Trivia DB quiz generator & spoken scorer |
| **Human Escalations** | [`src/escalations.py`](src/escalations.py) | Mentor ticket generation (`ESC-XXXX`), PII scrubber, and Ops page server |
| **Specialist Agents** | [`src/specialists.py`](src/specialists.py) | Kabir PID Coach agent definition & context briefing routing |
| **Static Intents** | [`src/static_intents.py`](src/static_intents.py) | Fast regex greetings/farewells (<50ms response) and spoken audio fillers |

---

## 🚀 Setup & Execution

### 1. Install Dependencies
```bash
cd backend
uv sync
```

### 2. Configure Environment
Copy `.env.example` to `.env.local`:
```bash
cp .env.example .env.local
```

Fill in your required credentials in `.env.local`:
```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret
MURF_API_KEY=your_murf_key
DEEPGRAM_API_KEY=your_deepgram_key
GOOGLE_API_KEY=your_google_key
```

### 3. Pre-download VAD & Turn Detector Models
```bash
uv run python src/agent.py download-files
```

### 4. Running the Backend
```bash
# Development mode with auto-reload
uv run python src/agent.py dev

# Terminal console testing mode (no frontend needed)
uv run python src/agent.py console

# Production worker mode
uv run python src/agent.py start
```

### 5. Running Secondary Operations
```bash
# Start Mentor Desk & Ops Page (http://127.0.0.1:8787)
uv run python src/escalations.py

# Print Call Analytics Summary
uv run python src/analytics.py
```

---

## 🧪 Testing Suite

Run all automated unit tests and LLM evaluation benchmarks:

```bash
uv run pytest
```

Test files are located in `tests/`:
- `test_agent.py` — Voice pipeline evals
- `test_analytics.py` — Call classification & PII sanitization checks
- `test_educational_tools.py` — Quiz dataset fallbacks
- `test_escalation.py` — Mentor ticket creation & consent gates
- `test_handoff.py` — Kabir PID Coach routing and handback checks
- `test_outbound.py` — Telephony dispatch opt-out validation

---

## 🐳 Container Deployment

Build and run using Docker:

```bash
docker build -t rishika-backend .
docker run --env-file .env.local rishika-backend
```

---

## 📄 License
MIT License
