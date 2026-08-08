'use client';

import { useEffect, useState } from 'react';
import { useTheme } from 'next-themes';
import { AnimatePresence, motion } from 'motion/react';
import { useAgent, useSessionContext } from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import { AgentSessionView_01 } from '@/components/agents-ui/blocks/agent-session-view-01';
import { WelcomeView } from '@/components/app/welcome-view';
import { ConnectingView } from '@/components/app/connecting-view';
import { EndedView } from '@/components/app/ended-view';

const MotionWelcomeView = motion.create(WelcomeView);
const MotionConnectingView = motion.create(ConnectingView);
const MotionSessionView = motion.create(AgentSessionView_01);
const MotionEndedView = motion.create(EndedView);

const VIEW_MOTION_PROPS = {
  variants: {
    visible: { opacity: 1, scale: 1, filter: 'blur(0px)' },
    hidden: { opacity: 0, scale: 0.97, filter: 'blur(6px)' },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: { duration: 0.45, ease: [0.16, 1, 0.3, 1] },
};

interface ViewControllerProps {
  appConfig: AppConfig;
}

export function ViewController({ appConfig }: ViewControllerProps) {
  const { isConnected, start } = useSessionContext();
  const { resolvedTheme } = useTheme();
  const { state: agentState } = useAgent();
  const [micError, setMicError] = useState<string | null>(null);
  const [hasHadActiveSession, setHasHadActiveSession] = useState(false);

  // Track active session to determine when a call ends
  const isConnecting = isConnected && (!agentState || agentState === 'initializing');
  const isAgentReady = isConnected && agentState && agentState !== 'initializing';

  useEffect(() => {
    if (isAgentReady) {
      setHasHadActiveSession(true);
    }
  }, [isAgentReady]);

  async function handleStart() {
    setMicError(null);
    setHasHadActiveSession(false);

    try {
      // Explicitly request audio stream within direct user gesture for mobile compatibility
      if (navigator.mediaDevices && typeof navigator.mediaDevices.getUserMedia === 'function') {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach((track) => track.stop());
      }
    } catch (err: any) {
      console.warn('Microphone permission check warning:', err);
      // Only set micError if permission was explicitly denied
      if (err?.name === 'NotAllowedError' || err?.name === 'PermissionDeniedError') {
        setMicError('Microphone access denied. Please allow mic access in browser settings.');
        return;
      }
    }

    // Call LiveKit session start
    try {
      start();
    } catch (err) {
      console.error('LiveKit start error:', err);
    }
  }

  function handleDismissMicError() {
    setMicError(null);
  }

  function handleGoHome() {
    setHasHadActiveSession(false);
  }

  const isEnded = !isConnected && hasHadActiveSession;

  return (
    <AnimatePresence mode="wait">
      {/* Welcome */}
      {!isConnected && !isEnded && (
        <MotionWelcomeView
          key="welcome"
          {...VIEW_MOTION_PROPS}
          startButtonText={appConfig.startButtonText}
          onStartCall={handleStart}
          micError={micError}
          onDismissMicError={handleDismissMicError}
        />
      )}

      {/* Connecting — shown while room is joined but agent hasn't spoken yet */}
      {isConnecting && (
        <MotionConnectingView
          key="connecting"
          {...VIEW_MOTION_PROPS}
        />
      )}

      {/* Live session */}
      {isAgentReady && (
        <MotionSessionView
          key="session-view"
          {...VIEW_MOTION_PROPS}
          supportsChatInput={appConfig.supportsChatInput}
          supportsVideoInput={appConfig.supportsVideoInput}
          supportsScreenShare={appConfig.supportsScreenShare}
          isPreConnectBufferEnabled={appConfig.isPreConnectBufferEnabled}
          audioVisualizerType={appConfig.audioVisualizerType}
          audioVisualizerColor={
            resolvedTheme === 'dark'
              ? appConfig.audioVisualizerColorDark
              : appConfig.audioVisualizerColor
          }
          audioVisualizerColorShift={appConfig.audioVisualizerColorShift}
          audioVisualizerBarCount={appConfig.audioVisualizerBarCount}
          audioVisualizerGridRowCount={appConfig.audioVisualizerGridRowCount}
          audioVisualizerGridColumnCount={appConfig.audioVisualizerGridColumnCount}
          audioVisualizerRadialBarCount={appConfig.audioVisualizerRadialBarCount}
          audioVisualizerRadialRadius={appConfig.audioVisualizerRadialRadius}
          audioVisualizerWaveLineWidth={appConfig.audioVisualizerWaveLineWidth}
          className="fixed inset-0"
        />
      )}

      {/* Ended / Exit Screen */}
      {isEnded && (
        <MotionEndedView
          key="ended"
          {...VIEW_MOTION_PROPS}
          onRestart={handleStart}
          onGoHome={handleGoHome}
        />
      )}
    </AnimatePresence>
  );
}
