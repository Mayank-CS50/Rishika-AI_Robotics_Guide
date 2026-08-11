# Project Handoff & Technical Summary (Current Standing)

## 📌 Executive Summary & Current Standing

This handoff document provides a complete, up-to-date summary of the **Murf Falcon + LiveKit Voice Agent (Rishika - LFR Teaching Assistant)** repository standing as of **Day 5 Completion**.

- **Current Status**: **Days 1 to 5 Fully Completed & Verified**
- **Next Challenge**: **Day 6 (Outbound Telephony Calls via LiveKit SIP / Twilio)**

---

## 🛠️ Complete Feature Matrix & Standing

### 1. Core Voice Pipeline (Days 1 – 3)
- **STT**: Deepgram Nova-3 (`language="multi"` for bilingual English/Devanagari Hindi).
- **TTS**: **Murf Falcon** (`voice="Anisha"`, `locale="en-IN"`, `style="Casual"`) for ultra-low latency voice streaming.
- **LLM**: Google Gemini 3.5 Flash Lite with slimmed Rishika LFR Teaching Assistant prompt.
- **Turn Detection & VAD**: Multilingual turn detector + Silero VAD.

### 2. Day 4: Memory & Student Profiles
- **Database Module**: [`backend/src/db_memory.py`](file:///d:/Lvlup%20Sem%20comin/murf-livekit-starter/backend/src/db_memory.py) (SQLite persistent store).
- **Tools**:
  - `lookup_user`: Retrieves returning caller progress, past LFR topics, and mistakes noted.
  - `save_user_memory`: Requires explicit user consent before storing progress.
  - `forget_user_memory`: Wipes user profile on request.

### 3. Day 5: Live Tools, Knowledge Scorer & Interactive Clickable MCQ UI
- **Educational Tools Module**: [`backend/src/educational_tools.py`](file:///d:/Lvlup%20Sem%20comin/murf-livekit-starter/backend/src/educational_tools.py)
  - `lookup_word_definition`: Queries live Free Dictionary API with 3.0s timeout and graceful out-loud failure handling.
  - `fetch_educational_quiz`: Queries live Open Trivia DB with topic chaining (links Day 4 student progress to Day 5 quiz difficulty) and fallback to local `LOCAL_FALLBACK_QUIZ` dataset.
  - `evaluate_answer_score`: Knowledge rating tool (`score_spoken_answer`) that evaluates student accuracy (0-100%) and provides concise 1-2 sentence feedback.
- **Pre-Execution Audio Fillers**: [`backend/src/static_intents.py`](file:///d:/Lvlup%20Sem%20comin/murf-livekit-starter/backend/src/static_intents.py) (*"Ek second, main dictionary check kar rahi hun..."*).
- **Live UI Data Channel Push**: Broadcasts `TOOL_RESULT_CARD` JSON payloads over LiveKit data channel.
- **Interactive Clickable MCQ Window**: [`frontend/components/agents-ui/tool-data-card.tsx`](file:///d:/Lvlup%20Sem%20comin/murf-livekit-starter/frontend/components/agents-ui/tool-data-card.tsx)
  - Built with Shadcn UI interactive clickable option buttons.
  - **Instant Visual Feedback**: Emerald Green for correct selection, Vibrant Red for incorrect selection.
  - **Voice Sync**: Clicking options auto-replies to LiveKit session so Rishika acknowledges out loud.

### 4. UI/UX Optimizations (Phases 1 – 5)
- **Fast Regex Intent Interceptor**: Direct ~50ms TTS response for pure greetings (`hi`, `namaste`) and farewells (`bye`, `alvida`) with **0 LLM token cost**.
- **Glassmorphism & Aura Layering**: `.glass-card` chat container overlaid on the `Aura` visualizer (`scale: 1`).
- **Chat Top/Bottom Scroll-Fade**: `.scroll-fade-y` CSS gradient mask.
- **Shimmer Text Loading Indicator**: Animated Shimmer text during agent thinking, initializing, and tool execution states.
- **Accessibility Tooltips**: Radix tooltips on lower control bar buttons.
- **Seamless 3D Spline Landing Page**: [`frontend/components/app/welcome-view.tsx`](file:///d:/Lvlup%20Sem%20comin/murf-livekit-starter/frontend/components/app/welcome-view.tsx) featuring a blended 3D Spline scene (`mix-blend-mode: screen`, radial mask) with Framer Motion transition morphing to the active session view.

---

## 🗺️ Roadmap: Day 6 (Make Outbound Calls)

| Step | Requirement | Status |
| :--- | :--- | :--- |
| **Step 1** | Define Learning & Literacy Outbound Use Case (Daily LFR Practice Call) | Ready ⏳ |
| **Step 2** | Integrate LiveKit Telephony / SIP Outbound Dispatch Script (`dispatch_outbound.py`) | Pending ⏳ |
| **Step 3** | Implement Outbound Opening Script (Who is calling, why, opt-out instructions) | Pending ⏳ |
| **Step 4** | Test Outbound Call to phone number & verify voice interaction | Pending ⏳ |

---

## 🚀 How to Run & Verify Current Project

### Backend (Python)
```powershell
cd backend
# Dev mode (auto-reload)
uv run python src/agent.py dev

# Terminal console mode
uv run python src/agent.py console

# Unit tests
python -m pytest tests/test_educational_tools.py
```

### Frontend (Next.js)
```powershell
cd frontend
pnpm dev
```
Open [http://localhost:3000](http://localhost:3000) in browser.
