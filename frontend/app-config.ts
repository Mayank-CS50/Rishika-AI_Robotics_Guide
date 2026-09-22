export interface AppConfig {
  pageTitle: string;
  pageDescription: string;
  companyName: string;

  supportsChatInput: boolean;
  supportsVideoInput: boolean;
  supportsScreenShare: boolean;
  isPreConnectBufferEnabled: boolean;

  logo: string;
  startButtonText: string;
  accent?: string;
  logoDark?: string;
  accentDark?: string;

  audioVisualizerType?: 'bar' | 'wave' | 'grid' | 'radial' | 'aura';
  audioVisualizerColor?: `#${string}`;
  audioVisualizerColorDark?: `#${string}`;
  audioVisualizerColorShift?: number;
  audioVisualizerBarCount?: number;
  audioVisualizerGridRowCount?: number;
  audioVisualizerGridColumnCount?: number;
  audioVisualizerRadialBarCount?: number;
  audioVisualizerRadialRadius?: number;
  audioVisualizerWaveLineWidth?: number;

  // agent dispatch configuration
  agentName?: string;

  // LiveKit Cloud Sandbox configuration
  sandboxId?: string;
}

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
  logoDark: '/logo.png',
  accentDark: '#EC4899',
  startButtonText: 'START LAB QUEST [▶]',

  audioVisualizerType: 'aura',
  audioVisualizerColor: '#EC4899',
  audioVisualizerColorDark: '#EC4899',
  audioVisualizerColorShift: 0.3,
  audioVisualizerWaveLineWidth: 3,

  agentName: process.env.AGENT_NAME ?? undefined,
  sandboxId: undefined,
};
