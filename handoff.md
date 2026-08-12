# Project Handoff & Technical Summary (Current Standing)

## 📌 Executive Summary & Current Standing

This handoff document provides a complete, up-to-date summary of the **Murf Falcon + LiveKit Voice Agent (Rishika - LFR Teaching Assistant)** repository standing as of **Day 7 Completion**.

- **Current Status**: **Days 1 to 7 Code Complete** (Day 6 real phone call blocked on Twilio credentials — see below)
- **Next Action**: Record the Day 7 video (browser session is enough), then finish the Day 6 call when a number is available.

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

## 🗺️ Day 6: Outbound Calls (Code Complete, Awaiting Twilio Credentials)

**Use case**: Daily LFR practice call — Rishika rings a learner at a chosen time, asks one quiz
question drawn from their Day 4 saved topic, scores it, and encourages them.

| Step | Requirement | Status |
| :--- | :--- | :--- |
| **Step 1** | Learning & Literacy outbound use case (daily LFR practice call) | Done ✅ |
| **Step 2** | LiveKit SIP outbound dial + dispatch script | Done ✅ |
| **Step 3** | Opening script (who / why / how to stop) | Done ✅ |
| **Step 4** | Place real call to a phone & verify voice interaction | **Blocked — needs Twilio account** ⛔ |
| **Step 5–7** | Record video, post to LinkedIn, submit form | Pending (manual) ⏳ |

### New files
- [`backend/src/setup_sip_trunk.py`](file:///d:/Lvlup%20Sem%20comin/murf-livekit-starter/backend/src/setup_sip_trunk.py) — one-time Twilio→LiveKit trunk registration. Idempotent: re-running prints the existing trunk id instead of creating a duplicate.
- [`backend/src/dispatch_outbound.py`](file:///d:/Lvlup%20Sem%20comin/murf-livekit-starter/backend/src/dispatch_outbound.py) — `--to +91... [--name Ramesh]`. Loads the learner's saved profile so the opening references their real last topic. Refuses to dial opted-out numbers.
- [`backend/tests/test_outbound.py`](file:///d:/Lvlup%20Sem%20comin/murf-livekit-starter/backend/tests/test_outbound.py) — offline checks for opt-out persistence and disclosure completeness.

### Changed
- `agent.py` — reads `ctx.job.metadata` for the number; dials via `ctx.api.sip.create_sip_participant`
  with `wait_until_answered=True`, 30s ring timeout, 10min call cap; waits for the callee to actually
  join before starting the session (otherwise the greeting plays into a ringing line). `TwirpError`
  covers no-answer / busy / rejected / trunk failure and calls `ctx.shutdown()` to release the job.
  New `stop_calling_me` tool persists the opt-out and hangs up. Web sessions are untouched — the
  outbound prompt rules and SIP path only activate when metadata carries a phone number.
- `static_intents.py` — `outbound_opening()` builds the disclosure; spoken via `session.say()` so the
  LLM cannot paraphrase away the opt-out line.
- `db_memory.py` — `opt_outs` table with number normalization (`+91 98765-43210` == `+919876543210`).
  `get_connection()` is now a context manager that closes the handle; the previous version leaked one
  file handle per tool call.

### Finish Day 6
```powershell
# 1. Twilio Console -> Elastic SIP Trunking -> create trunk + credential list, buy a number
# 2. Fill TWILIO_* vars in backend/.env.local (see .env.example)
cd backend
uv run python src/setup_sip_trunk.py          # prints SIP_OUTBOUND_TRUNK_ID -> paste into .env.local
uv run python src/agent.py start              # use `start`, not `dev`, for phone testing
uv run python src/dispatch_outbound.py --to +91XXXXXXXXXX --name Ramesh
```

### Not built (say the word if you want them)
- Answering-machine detection — voicemail is indistinguishable from a human at the SIP layer.
- Retry scheduling on no-answer, and CSV campaign mode. Single call covers the Day 6 requirement.

---

## 🙋 Day 7: Know When to Ask for Human Help (Complete)

**Two escalation reasons only** (Learning & Literacy track), both of which Rishika already
recognised in her prompt but previously had no action for:

| Reason key | Trigger |
| :--- | :--- |
| `learner_distress` | Learner is crying, panicking, quitting, or the self-doubt returns after one round of encouragement |
| `needs_human_mentor` | Hands-on hardware fault: burning smell, hot motor driver, smoke, broken joint, wheels dead after the wiring/threshold checks |

Everything else — normal doubts, quizzes, PID logic — she still handles herself. Difficulty alone is not a reason to escalate.

| Step | Requirement | Status |
| :--- | :--- | :--- |
| **Step 1** | Two reasons for human help | Done ✅ |
| **Step 2** | `create_escalation` tool | Done ✅ |
| **Step 3** | Short summary: who / what / already checked / urgency / language / follow-up | Done ✅ |
| **Step 4** | Consent asked before sharing, refusal creates nothing | Done ✅ (enforced in code, not just the prompt) |
| **Step 5** | Sent somewhere real | Done ✅ SQLite + mentor desk page, plus Discord/Slack webhook if configured |
| **Step 6** | Reference ID + honest next step | Done ✅ `ESC-XXXX`, "within one working day", never "right now" |
| **Step 7** | Both paths tested | Done ✅ `tests/test_escalation.py` (8 checks) + live browser session |
| **Step 8–10** | Video, LinkedIn, form | Pending (manual) ⏳ |

### New files
- [`backend/src/escalations.py`](file:///d:/Lvlup%20Sem%20comin/murf-livekit-starter/backend/src/escalations.py) — the whole Day 7 backend in one module: `escalations` table (reuses `db_memory.get_connection`), PII scrub, dedupe, webhook delivery, and the mentor desk page served from stdlib `http.server`. No new dependencies.
- [`backend/tests/test_escalation.py`](file:///d:/Lvlup%20Sem%20comin/murf-livekit-starter/backend/tests/test_escalation.py) — offline checks for both paths.

### Changed
- `agent.py` — `DAY 7 HUMAN HANDOFF RULES` in the system prompt; new `create_escalation` and `check_escalation_status` tools. The tool refuses to write anything unless `consent_confirmed` is true, and `escalations.create_or_update()` re-checks it, so an LLM that forgets to ask cannot create a row.
- `static_intents.py` — `ESCALATION_FILLER` spoken while the request is being written.
- `tool-data-card.tsx` — `escalation` card type: reference ID, urgency, status, and the summary exactly as the mentor sees it.
- `.env.example` — `ESCALATION_WEBHOOK_URL` (optional), `ESCALATION_DESK_PORT`.

### Advanced extras included
Urgency levels (`low`/`medium`/`high`/`emergency`, mis-specified values fall back to `medium`),
PII redaction (phone numbers, OTPs, PINs, account numbers stripped before storage — `L298N` and
`PID` survive), duplicate suppression (same learner + same reason updates the open request and
returns the same reference ID), and status tracking (`open` → `in_progress` → `resolved`, readable
back to the learner by voice).

### Run Day 7
```powershell
cd backend
uv run python src/escalations.py            # mentor desk -> http://127.0.0.1:8787
uv run python src/agent.py dev              # separate terminal
python -m pytest tests/test_escalation.py

# mentor actions
uv run python src/escalations.py --list
uv run python src/escalations.py --start ESC-4F2A
uv run python src/escalations.py --resolve ESC-4F2A
```
Optional: paste a Discord webhook URL into `ESCALATION_WEBHOOK_URL` in `.env.local` and the
summary is posted to the channel too. The desk page is read-only and binds to `127.0.0.1` only —
it has no auth, so do not expose it.

### Demo script for the video
1. **Normal path** — "मेरा रोबोट लाइन पर वॉबल कर रहा है" → she debugs it herself, no request created, desk page stays empty.
2. **Escalation path** — "L298N बहुत गरम हो रहा है और जलने की स्मेल आ रही है" → she stops debugging, lists what she will send, asks permission.
3. Say **no** first → she drops the notes, nothing appears on the desk.
4. Say **yes** → filler audio, `ESC-XXXX` read out slowly, UI card appears, row appears on the mentor desk (and in Discord).

### Not built
- Auto callback on resolution (the Day 6 dispatch script can do it manually: `--to <number>`).
- Email/help-desk integrations — the webhook covers Discord and Slack, which is enough.

---


## 🚀 How to Run & Verify Current Project

### Backend (Python)
```powershell
cd backend
# Dev mode (auto-reload)
uv run python src/agent.py dev

# Terminal console mode
uv run python src/agent.py console

# Mentor desk (Day 7) — separate terminal
uv run python src/escalations.py

# Unit tests
python -m pytest tests
```

### Frontend (Next.js)
```powershell
cd frontend
pnpm dev
```
Open [http://localhost:3000](http://localhost:3000) in browser.
