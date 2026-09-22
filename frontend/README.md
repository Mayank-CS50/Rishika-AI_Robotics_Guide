# Rishika Frontend — Voice AI UI & 3D Interactive Interface

The React & Next.js 15 frontend for **Rishika (Voice AI LFR Teaching Assistant)**. Built with Next.js Turbopack, Framer Motion, 3D WebGL Spline scenes, and [LiveKit Agents UI](https://livekit.io/ui) components, it provides a high-performance interactive interface for real-time voice conversations, clickable MCQ quiz cards, and mentor ticket feedback.

---

## 🎨 Features & Capabilities

- **Real-Time Audio Visualizer**: Aura shader-based visualizer with dynamic color shifts.
- **Interactive Clickable MCQ Cards**: Custom tool result cards (`tool-data-card.tsx`) that display LiveKit quiz payloads with emerald/red feedback and voice-synced option triggers.
- **3D Spline Landing Page**: Seamless blended 3D background morphing into active session view (`welcome-view.tsx`).
- **Glassmorphism Chat Experience**: Overlay glassmorphic transcript pane with scroll-fade masks and shimmer loading indicators.
- **Theme Support**: System preference dark/light mode with customized accent colors.

---

## 🚀 Setup & Execution

### 1. Install Dependencies
```bash
cd frontend
pnpm install
```

### 2. Configure Environment
Copy `.env.example` to `.env.local`:
```bash
cp .env.example .env.local
```

Set your LiveKit credentials in `.env.local`:
```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret
AGENT_NAME=my-agent
```

### 3. Start Development Server
```bash
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser. Ensure the Rishika backend service is running concurrently.

---

## ⚙️ Customization (`app-config.ts`)

UI titles, branding, and audio visualizer parameters are managed centrally in [`app-config.ts`](app-config.ts):

```ts
export const APP_CONFIG_DEFAULTS: AppConfig = {
  companyName: 'RISHIKA VOICE LABS',
  pageTitle: 'Rishika — Voice AI LFR Teaching Assistant',
  pageDescription: 'Hindi-first real-time voice teaching assistant for Line Follower Robots',

  supportsChatInput: true,
  supportsVideoInput: false,
  supportsScreenShare: false,
  isPreConnectBufferEnabled: true,

  logo: '/logo.png',
  accent: '#EC4899',
  startButtonText: 'START LAB QUEST [▶]',
  audioVisualizerType: 'aura',
};
```

---

## 📂 Project Structure

```
frontend/
├── app/
│   ├── page.tsx                # Main application page
│   ├── layout.tsx              # Root HTML layout & font definitions
│   └── api/token/route.ts      # LiveKit JWT token generation endpoint
├── components/
│   ├── agents-ui/              # LiveKit audio visualizers & custom tool cards
│   ├── app/                    # Welcome view, 3D Spline canvas & view controller
│   └── ui/                     # Primitive shadcn UI elements
├── hooks/                      # Custom audio & session state hooks
├── styles/                     # Global CSS tokens & glassmorphism utilities
├── app-config.ts               # Branding & feature flags
└── package.json                # Dependencies & scripts
```

---

## 📄 License
MIT License
