'use client';

import { type ComponentProps, useRef } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { type AgentState, type ReceivedMessage } from '@livekit/components-react';
import { AgentChatIndicator } from '@/components/agents-ui/agent-chat-indicator';
import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from '@/components/ai-elements/conversation';
import { MessageContent, MessageResponse } from '@/components/ai-elements/message';
import { Shimmer } from '@/components/ai-elements/shimmer';
import { cn } from '@/lib/shadcn/utils';

/**
 * Day 9: two agents share one room participant, so the only way to tell them apart in
 * the transcript is the `active_agent` attribute the backend publishes on handoff.
 * Class strings are literal on purpose — Tailwind cannot see interpolated colours.
 */
const AGENTS = {
  rishika: {
    label: '[ RISHIKA // TA ]',
    header: 'text-[#EC4899]',
    badge: 'border-[#EC4899]/40 text-[#EC4899]',
    bubble: 'border-[#EC4899]/40 shadow-[0_4px_16px_rgba(236,72,153,0.12)]',
    dot: 'bg-[#EC4899]',
    panel: 'border-[#EC4899]/50 shadow-[0_0_20px_rgba(236,72,153,0.2)]',
    shimmer: 'text-[#EC4899]',
    scroll:
      'border-2 border-[#EC4899]/60 bg-[#080710]/90 text-[#EC4899] shadow-[3px_3px_0px_0px_#EC4899] hover:bg-[#EC4899] hover:text-white',
    working: '[ RISHIKA IS PROCESSING & FETCHING RESOURCES... ]',
  },
  kabir: {
    label: '[ KABIR // P.I.D TUNING SPECIALIST ]',
    header: 'text-[#22D3EE]',
    badge: 'border-[#22D3EE]/40 text-[#22D3EE]',
    bubble: 'border-[#22D3EE]/40 shadow-[0_4px_16px_rgba(34,211,238,0.12)]',
    dot: 'bg-[#22D3EE]',
    panel: 'border-[#22D3EE]/50 shadow-[0_0_20px_rgba(34,211,238,0.2)]',
    shimmer: 'text-[#22D3EE]',
    scroll:
      'border-2 border-[#22D3EE]/60 bg-[#080710]/90 text-[#22D3EE] shadow-[3px_3px_0px_0px_#22D3EE] hover:bg-[#22D3EE] hover:text-white',
    working: '[ KABIR IS WORKING OUT THE GAINS... ]',
  },
} as const;

type AgentKey = keyof typeof AGENTS;

export interface AgentChatTranscriptProps extends ComponentProps<'div'> {
  agentState?: AgentState;
  messages?: ReceivedMessage[];
  /** `active_agent` room attribute — 'kabir' while the specialist holds the call. */
  activeAgent?: string;
  className?: string;
}

export function AgentChatTranscript({
  agentState,
  messages = [],
  activeAgent,
  className,
  ...props
}: AgentChatTranscriptProps) {
  const current: AgentKey = activeAgent === 'kabir' ? 'kabir' : 'rishika';
  // Whoever was speaking when a message first appeared owns it forever, so the
  // handoff leaves Rishika's earlier bubbles pink instead of recolouring history.
  const spokenBy = useRef(new Map<string, AgentKey>());

  return (
    <Conversation className={cn('w-full font-mono scroll-fade-y', className)} {...props}>

      <ConversationContent className="gap-4 px-4 pt-32 pb-6 md:px-8">
        {messages.map((receivedMessage, idx) => {
          const { id, timestamp, from, message } = receivedMessage;
          const isUser = from?.isLocal === true;
          const key = id || `msg-${idx}`;
          if (!isUser && !spokenBy.current.has(key)) {
            spokenBy.current.set(key, current);
          }
          const speaker = AGENTS[spokenBy.current.get(key) ?? current];
          const time = new Date(timestamp);
          const timeStr = time.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true,
          });

          return (
            <motion.div
              key={key}
              initial={{ opacity: 0, y: 10, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.25, ease: 'easeOut' }}
              className={cn(
                'group flex w-full max-w-[82%] flex-col gap-1 md:max-w-[68%]',
                isUser ? 'ml-auto items-end justify-end' : 'mr-auto items-start justify-start'
              )}
            >
              {/* Header Badges: Sender + Timestamp */}
              <div
                className={cn(
                  'flex items-center gap-2 text-[9px] tracking-wider uppercase font-mono select-none mb-0.5',
                  isUser ? 'flex-row-reverse text-[#10B981]' : cn('flex-row', speaker.header)
                )}
              >
                <span
                  className={cn(
                    'px-2 py-0.5 border rounded-full font-bold bg-[#080710]/90 backdrop-blur-md',
                    isUser ? 'border-[#10B981]/40 text-[#10B981]' : speaker.badge
                  )}
                >
                  {isUser ? '[ USER ]' : speaker.label}
                </span>
                <span className="text-foreground/40 text-[9px] font-mono">{timeStr}</span>
              </div>

              {/* Message Bubble — Rounded Crystal Glassmorphic */}
              <div
                className={cn(
                  'w-fit max-w-full p-3.5 text-xs md:text-sm font-mono leading-relaxed transition-all duration-200',
                  'bg-[#0c0a18]/90 backdrop-blur-xl border shadow-lg text-[#FAF6F0] rounded-2xl',
                  isUser
                    ? 'rounded-tr-xs border-[#10B981]/40 shadow-[0_4px_16px_rgba(16,185,129,0.12)]'
                    : cn('rounded-tl-xs', speaker.bubble)
                )}
              >
                <MessageContent className="p-0 bg-transparent text-inherit group-[.is-user]:bg-transparent group-[.is-user]:p-0">
                  <MessageResponse className="text-inherit">{message}</MessageResponse>
                </MessageContent>
              </div>
            </motion.div>
          );
        })}

        {/* Thinking / Tool Execution State Shimmer Indicator */}
        <AnimatePresence>
          {(agentState === 'thinking' || agentState === 'initializing') && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className={cn(
                'flex items-center gap-3 p-3 border bg-[#080710]/90 backdrop-blur-xl rounded-xl w-fit',
                AGENTS[current].panel
              )}
            >
              <AgentChatIndicator size="sm" className={AGENTS[current].dot} />
              <Shimmer
                duration={1.5}
                className={cn(
                  'text-xs font-mono tracking-widest uppercase font-bold',
                  AGENTS[current].shimmer
                )}
              >
                {agentState === 'thinking'
                  ? AGENTS[current].working
                  : '[ INITIALIZING VOICE PIPELINE... ]'}
              </Shimmer>
            </motion.div>
          )}
        </AnimatePresence>
      </ConversationContent>
      <ConversationScrollButton className={AGENTS[current].scroll} />
    </Conversation>
  );
}
