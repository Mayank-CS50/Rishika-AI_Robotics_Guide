'use client';

import React, { useEffect, useRef, useState } from 'react';
import { AnimatePresence, type MotionProps, motion } from 'motion/react';
import {
  useAgent,
  useIsSpeaking,
  useLocalParticipant,
  useSessionContext,
  useSessionMessages,
  useTrackVolume,
} from '@livekit/components-react';
import { Track } from 'livekit-client';
import { AgentChatTranscript } from '@/components/agents-ui/agent-chat-transcript';
import {
  AgentControlBar,
  type AgentControlBarControls,
} from '@/components/agents-ui/agent-control-bar';
import { ToolDataCard } from '@/components/agents-ui/tool-data-card';
import { Shimmer } from '@/components/ai-elements/shimmer';
import { cn } from '@/lib/shadcn/utils';
import { TileLayout } from './tile-view';

const MotionMessage = motion.create(Shimmer);

const BOTTOM_VIEW_MOTION_PROPS: MotionProps = {
  variants: {
    visible: {
      opacity: 1,
      translateY: '0%',
    },
    hidden: {
      opacity: 0,
      translateY: '100%',
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: {
    duration: 0.3,
    delay: 0.5,
    ease: 'easeOut',
  },
};

const CHAT_MOTION_PROPS: MotionProps = {
  variants: {
    hidden: {
      opacity: 0,
      transition: {
        ease: 'easeOut',
        duration: 0.3,
      },
    },
    visible: {
      opacity: 1,
      transition: {
        delay: 0.2,
        ease: 'easeOut',
        duration: 0.3,
      },
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
};

const SHIMMER_MOTION_PROPS: MotionProps = {
  variants: {
    visible: {
      opacity: 1,
      transition: {
        ease: 'easeIn',
        duration: 0.5,
        delay: 0.8,
      },
    },
    hidden: {
      opacity: 0,
      transition: {
        ease: 'easeIn',
        duration: 0.5,
        delay: 0,
      },
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
};

interface FadeProps {
  top?: boolean;
  bottom?: boolean;
  className?: string;
}

export function Fade({ top = false, bottom = false, className }: FadeProps) {
  return (
    <div
      className={cn(
        'from-background pointer-events-none h-4 bg-linear-to-b to-transparent',
        top && 'bg-linear-to-b',
        bottom && 'bg-linear-to-t',
        className
      )}
    />
  );
}

export interface AgentSessionView_01Props {
  /**
   * Message shown above the controls before the first chat message is sent.
   *
   * @default 'Agent is listening, ask it a question'
   */
  preConnectMessage?: string;
  /**
   * Enables or disables the chat toggle and transcript input controls.
   *
   * @default true
   */
  supportsChatInput?: boolean;
  /**
   * Enables or disables camera controls in the bottom control bar.
   *
   * @default true
   */
  supportsVideoInput?: boolean;
  /**
   * Enables or disables screen sharing controls in the bottom control bar.
   *
   * @default true
   */
  supportsScreenShare?: boolean;
  /**
   * Shows a pre-connect buffer state with a shimmer message before messages appear.
   *
   * @default true
   */
  isPreConnectBufferEnabled?: boolean;

  /** Selects the visualizer style rendered in the main tile area. */
  audioVisualizerType?: 'bar' | 'wave' | 'grid' | 'radial' | 'aura';
  /** Primary hex color used by supported audio visualizer variants. */
  audioVisualizerColor?: `#${string}`;
  /** Hue shift intensity used by certain visualizers. */
  audioVisualizerColorShift?: number;
  /** Number of bars to render when `audioVisualizerType` is `bar`. */
  audioVisualizerBarCount?: number;
  /** Number of rows in the visualizer when `audioVisualizerType` is `grid`. */
  audioVisualizerGridRowCount?: number;
  /** Number of columns in the visualizer when `audioVisualizerType` is `grid`. */
  audioVisualizerGridColumnCount?: number;
  /** Number of radial bars when `audioVisualizerType` is `radial`. */
  audioVisualizerRadialBarCount?: number;
  /** Base radius of the radial visualizer when `audioVisualizerType` is `radial`. */
  audioVisualizerRadialRadius?: number;
  /** Stroke width of the wave path when `audioVisualizerType` is `wave`. */
  audioVisualizerWaveLineWidth?: number;
  /** Optional class name merged onto the outer `<section>` container. */
  className?: string;
}

export function AgentSessionView_01({
  preConnectMessage = 'Agent is listening, ask it a question',
  supportsChatInput = true,
  supportsVideoInput = true,
  supportsScreenShare = true,
  isPreConnectBufferEnabled = true,

  audioVisualizerType,
  audioVisualizerColor,
  audioVisualizerColorShift,
  audioVisualizerBarCount,
  audioVisualizerGridRowCount,
  audioVisualizerGridColumnCount,
  audioVisualizerRadialBarCount,
  audioVisualizerRadialRadius,
  audioVisualizerWaveLineWidth,
  ref,
  className,
  ...props
}: React.ComponentProps<'section'> & AgentSessionView_01Props) {
  const session = useSessionContext();
  const { messages } = useSessionMessages(session);
  const [chatOpen, setChatOpen] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const { state: agentState, internal } = useAgent();
  // Day 9: set by the backend on handoff — 'kabir' while the P.I.D specialist is live.
  // Read the participant's own map, NOT useAgent().attributes: that hook stores only the
  // keys of the last AttributesChanged event, and the framework rewrites lk.agent.state on
  // every listening/thinking/speaking flip, which wipes active_agent within a second.
  const activeAgent = internal.agentParticipant?.attributes.active_agent;

  // Significant speech volume detection for user mic glow (filtering out background noise)
  const { localParticipant } = useLocalParticipant();
  const isUserSpeaking = useIsSpeaking(localParticipant);
  const micPublication = localParticipant?.getTrackPublication(Track.Source.Microphone);
  const micVolume = useTrackVolume(micPublication?.track as any);

  // Trigger right emerald glow ONLY on significant vocal speech (volume > 0.10)
  const isSignificantUserSpeech =
    agentState === 'listening' && (isUserSpeaking || micVolume > 0.12) && micVolume > 0.06;

  const controls: AgentControlBarControls = {
    leave: true,
    microphone: true,
    chat: supportsChatInput,
    camera: supportsVideoInput,
    screenShare: supportsScreenShare,
  };

  useEffect(() => {
    const lastMessage = messages.at(-1);
    const lastMessageIsLocal = lastMessage?.from?.isLocal === true;

    if (scrollAreaRef.current && lastMessageIsLocal) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <section
      ref={ref}
      className={cn('bg-background relative z-10 h-full w-full overflow-hidden', className)}
      {...props}
    >
      <ToolDataCard />
      <Fade top className="absolute inset-x-4 top-0 z-10 h-40" />

      {/* High-Contrast Bright Side Glow Simulation Overlays */}
      <AnimatePresence>
        {/* User Speaking: Vibrant Emerald Green Glow on RIGHT SIDE (Only on significant speech) */}
        {isSignificantUserSpeech && (
          <motion.div
            key="right-user-speaking-sim"
            initial={{ opacity: 0, x: 50, scale: 0.85 }}
            animate={{
              opacity: [0.7, 1, 0.7],
              x: 0,
              scale: [0.98, 1.06, 0.98],
            }}
            exit={{ opacity: 0, x: 50, scale: 0.85 }}
            transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
            className="fixed right-0 top-1/2 -translate-y-1/2 w-56 md:w-96 h-[80vh] bg-gradient-to-l from-[#10B981]/90 via-[#10B981]/45 to-transparent blur-[60px] pointer-events-none z-20 rounded-l-full shadow-[0_0_80px_#10B981]"
          />
        )}

        {/* Agent Speaking or Thinking: Magenta for Rishika, cyan while Kabir has the call */}
        {(agentState === 'speaking' || agentState === 'thinking') && (
          <motion.div
            key="left-agent-speaking-sim"
            initial={{ opacity: 0, x: -50, scale: 0.85 }}
            animate={{
              opacity: [0.7, 1, 0.7],
              x: 0,
              scale: [0.98, 1.06, 0.98],
            }}
            exit={{ opacity: 0, x: -50, scale: 0.85 }}
            transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
            className={cn(
              'fixed left-0 top-1/2 -translate-y-1/2 w-56 md:w-96 h-[80vh] blur-[60px] pointer-events-none z-20 rounded-r-full bg-gradient-to-r',
              activeAgent === 'kabir'
                ? 'from-[#22D3EE]/90 via-[#22D3EE]/45 to-transparent shadow-[0_0_80px_#22D3EE]'
                : 'from-[#EC4899]/90 via-[#EC4899]/45 to-transparent shadow-[0_0_80px_#EC4899]'
            )}
          />
        )}
      </AnimatePresence>

      {/* transcript container overlaid on background visualizer */}
      <div className="absolute inset-x-0 top-6 bottom-[135px] flex w-full flex-col items-center justify-center px-4 md:bottom-[170px] z-20 pointer-events-none">
        <AnimatePresence>
          {chatOpen && (
            <motion.div
              {...CHAT_MOTION_PROPS}
              className="glass-card pointer-events-auto flex h-full w-full max-w-3xl flex-col gap-4 p-4 md:p-6 rounded-3xl transition-all duration-300 ease-out shadow-2xl"
            >
              <AgentChatTranscript
                agentState={agentState}
                messages={messages}
                activeAgent={activeAgent}
                className="mx-auto w-full h-full"
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Tile layout */}
      <TileLayout
        chatOpen={chatOpen}
        audioVisualizerType={audioVisualizerType}
        audioVisualizerColor={audioVisualizerColor}
        audioVisualizerColorShift={audioVisualizerColorShift}
        audioVisualizerBarCount={audioVisualizerBarCount}
        audioVisualizerRadialBarCount={audioVisualizerRadialBarCount}
        audioVisualizerRadialRadius={audioVisualizerRadialRadius}
        audioVisualizerGridRowCount={audioVisualizerGridRowCount}
        audioVisualizerGridColumnCount={audioVisualizerGridColumnCount}
        audioVisualizerWaveLineWidth={audioVisualizerWaveLineWidth}
      />
      {/* Bottom */}
      <motion.div
        {...BOTTOM_VIEW_MOTION_PROPS}
        className="absolute inset-x-3 bottom-0 z-50 md:inset-x-12"
      >
        {/* Pre-connect message */}
        {isPreConnectBufferEnabled && (
          <AnimatePresence>
            {messages.length === 0 && (
              <MotionMessage
                key="pre-connect-message"
                duration={2}
                aria-hidden={messages.length > 0}
                {...SHIMMER_MOTION_PROPS}
                className="pointer-events-none mx-auto block w-full max-w-2xl pb-4 text-center text-sm font-semibold"
              >
                {preConnectMessage}
              </MotionMessage>
            )}
          </AnimatePresence>
        )}
        <div
          className={cn(
            'bg-transparent relative mx-auto transition-all duration-300 ease-out pb-4 md:pb-8',
            chatOpen ? 'w-full max-w-lg' : 'max-w-xs md:max-w-sm'
          )}
        >
          <AgentControlBar
            variant="livekit"
            controls={controls}
            isChatOpen={chatOpen}
            isConnected={session.isConnected}
            onDisconnect={session.end}
            onIsChatOpenChange={setChatOpen}
          />
        </div>
      </motion.div>
    </section>
  );
}
