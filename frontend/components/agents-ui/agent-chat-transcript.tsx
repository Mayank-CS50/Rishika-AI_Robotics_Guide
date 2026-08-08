'use client';

import { type ComponentProps } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { type AgentState, type ReceivedMessage } from '@livekit/components-react';
import { AgentChatIndicator } from '@/components/agents-ui/agent-chat-indicator';
import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from '@/components/ai-elements/conversation';
import { MessageContent, MessageResponse } from '@/components/ai-elements/message';
import { cn } from '@/lib/shadcn/utils';

export interface AgentChatTranscriptProps extends ComponentProps<'div'> {
  agentState?: AgentState;
  messages?: ReceivedMessage[];
  className?: string;
}

export function AgentChatTranscript({
  agentState,
  messages = [],
  className,
  ...props
}: AgentChatTranscriptProps) {
  return (
    <Conversation className={cn('w-full font-mono', className)} {...props}>
      <ConversationContent className="gap-4 px-4 pt-32 pb-6 md:px-8">
        {messages.map((receivedMessage, idx) => {
          const { id, timestamp, from, message } = receivedMessage;
          const isUser = from?.isLocal === true;
          const time = new Date(timestamp);
          const timeStr = time.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true,
          });

          return (
            <motion.div
              key={id || `msg-${idx}`}
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
                  isUser ? 'flex-row-reverse text-[#10B981]' : 'flex-row text-[#EC4899]'
                )}
              >
                <span
                  className={cn(
                    'px-2 py-0.5 border rounded-full font-bold bg-[#080710]/90 backdrop-blur-md',
                    isUser
                      ? 'border-[#10B981]/40 text-[#10B981]'
                      : 'border-[#EC4899]/40 text-[#EC4899]'
                  )}
                >
                  {isUser ? '[ USER ]' : '[ RISHIKA // TA ]'}
                </span>
                <span className="text-foreground/40 text-[9px] font-mono">{timeStr}</span>
              </div>

              {/* Message Bubble — Rounded Crystal Glassmorphic */}
              <div
                className={cn(
                  'w-fit max-w-full p-3.5 text-xs md:text-sm font-mono leading-relaxed transition-all duration-200',
                  'bg-[#0c0a18]/90 backdrop-blur-xl border shadow-lg',
                  isUser
                    ? 'rounded-2xl rounded-tr-xs border-[#10B981]/40 text-[#FAF6F0] shadow-[0_4px_16px_rgba(16,185,129,0.12)]'
                    : 'rounded-2xl rounded-tl-xs border-[#EC4899]/40 text-[#FAF6F0] shadow-[0_4px_16px_rgba(236,72,153,0.12)]'
                )}
              >
                <MessageContent className="p-0 bg-transparent text-inherit group-[.is-user]:bg-transparent group-[.is-user]:p-0">
                  <MessageResponse className="text-inherit">{message}</MessageResponse>
                </MessageContent>
              </div>
            </motion.div>
          );
        })}

        {/* Thinking State Crystal Indicator */}
        <AnimatePresence>
          {agentState === 'thinking' && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="flex items-center gap-3 p-3 border-2 border-[#EC4899]/40 bg-[#080710]/90 backdrop-blur-xl w-fit shadow-[3px_3px_0px_0px_#EC4899]"
            >
              <AgentChatIndicator size="sm" className="bg-[#EC4899]" />
              <span className="text-xs font-mono tracking-widest text-[#EC4899] uppercase animate-pulse">
                [ RISHIKA IS THINKING... ]
              </span>
            </motion.div>
          )}
        </AnimatePresence>
      </ConversationContent>
      <ConversationScrollButton className="border-2 border-[#EC4899]/60 bg-[#080710]/90 text-[#EC4899] shadow-[3px_3px_0px_0px_#EC4899] hover:bg-[#EC4899] hover:text-white" />
    </Conversation>
  );
}

