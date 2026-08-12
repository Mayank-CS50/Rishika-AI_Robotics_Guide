'use client';

import { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { useChat, useRoomContext } from '@livekit/components-react';
import { RoomEvent } from 'livekit-client';
import { Award, BookOpen, CheckCircle, HelpCircle, LifeBuoy, X, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface ToolCardData {
  type: string;
  cardType: 'dictionary' | 'quiz' | 'score' | 'escalation';
  title: string;
  subtitle: string;
  data: {
    word?: string;
    definition?: string;
    example?: string;
    question?: string;
    options?: string[];
    answer?: string;
    score?: number;
    rating?: string;
    userAnswer?: string;
    feedback?: string;
    refId?: string;
    reason?: string;
    urgency?: string;
    status?: string;
    summary?: string;
    nextStep?: string;
  };
}

export function ToolDataCard() {
  const room = useRoomContext();
  const { send: sendChatMessage } = useChat();
  const [activeCard, setActiveCard] = useState<ToolCardData | null>(null);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [isAnswered, setIsAnswered] = useState(false);

  useEffect(() => {
    if (!room) return;

    const handleDataReceived = (payload: Uint8Array) => {
      try {
        const text = new TextDecoder().decode(payload);
        const parsed = JSON.parse(text);
        if (parsed && parsed.type === 'TOOL_RESULT_CARD') {
          setActiveCard(parsed as ToolCardData);
          setSelectedOption(null);
          setIsAnswered(false);
        }
      } catch (err) {
        // Ignore non-JSON data messages
      }
    };

    room.on(RoomEvent.DataReceived, handleDataReceived);
    return () => {
      room.off(RoomEvent.DataReceived, handleDataReceived);
    };
  }, [room]);

  if (!activeCard) return null;

  const { cardType, title, subtitle, data } = activeCard;

  const handleOptionClick = async (opt: string) => {
    if (isAnswered) return;
    setSelectedOption(opt);
    setIsAnswered(true);

    // Send selection back to agent
    try {
      if (sendChatMessage) {
        await sendChatMessage(`I selected option: "${opt}" for the quiz question.`);
      }
    } catch (e) {
      console.warn('Failed to send chat reply for quiz option:', e);
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -20, scale: 0.95 }}
        transition={{ duration: 0.35, ease: 'easeOut' }}
        className="fixed top-20 right-4 md:right-8 z-50 max-w-sm w-full p-5 bg-[#0c0a18]/95 backdrop-blur-2xl border-2 border-[#EC4899]/70 shadow-[0_8px_32px_rgba(236,72,153,0.35)] rounded-2xl font-mono text-white flex flex-col gap-3"
      >
        {/* Card Header */}
        <div className="flex items-center justify-between border-b border-white/10 pb-2">
          <div className="flex items-center gap-2">
            {cardType === 'dictionary' && <BookOpen className="size-4 text-[#10B981]" />}
            {cardType === 'quiz' && <HelpCircle className="size-4 text-[#EC4899]" />}
            {cardType === 'score' && <Award className="size-4 text-[#F59E0B]" />}
            {cardType === 'escalation' && <LifeBuoy className="size-4 text-red-400" />}
            <span className="text-[10px] font-bold tracking-widest text-[#EC4899] uppercase">
              {title}
            </span>
          </div>
          <button
            onClick={() => setActiveCard(null)}
            className="text-zinc-400 hover:text-white p-1 rounded-md hover:bg-white/10 transition-all"
            title="Close Card"
          >
            <X className="size-4" />
          </button>
        </div>

        {/* Subtitle Badge */}
        <div className="text-[9px] text-zinc-400 uppercase tracking-wider">
          {subtitle}
        </div>

        {/* Dictionary Card Body */}
        {cardType === 'dictionary' && (
          <div className="flex flex-col gap-2 text-xs leading-relaxed">
            <p className="text-zinc-200 font-sans">
              <strong className="text-[#10B981]">Definition: </strong>
              {data.definition}
            </p>
            {data.example && (
              <p className="text-zinc-400 italic text-[11px]">
                &quot;{data.example}&quot;
              </p>
            )}
          </div>
        )}

        {/* Score Evaluation Card Body */}
        {cardType === 'score' && (
          <div className="flex flex-col gap-2 text-xs">
            <div className="flex items-center justify-between p-2 rounded-xl bg-amber-500/10 border border-amber-500/30">
              <span className="text-[10px] font-bold text-amber-400 uppercase">{data.rating}</span>
              <span className="text-sm font-bold text-[#10B981]">{data.score}%</span>
            </div>
            {data.feedback && (
              <p className="text-zinc-300 text-[11px] font-sans leading-relaxed">
                {data.feedback}
              </p>
            )}
          </div>
        )}

        {/* Day 7 Human Mentor Handoff Card Body */}
        {cardType === 'escalation' && (
          <div className="flex flex-col gap-2 text-xs">
            <div className="flex items-center justify-between p-2 rounded-xl bg-red-500/10 border border-red-500/40">
              <span className="text-sm font-bold tracking-widest text-red-300">{data.refId}</span>
              <span className="text-[10px] font-bold text-red-400 uppercase">
                {data.urgency} · {data.status}
              </span>
            </div>
            {data.summary && (
              <pre className="text-[10px] leading-relaxed text-zinc-300 whitespace-pre-wrap font-mono">
                {data.summary}
              </pre>
            )}
            {data.nextStep && (
              <p className="text-[10px] text-zinc-400 font-sans border-t border-white/10 pt-2">
                {data.nextStep}
              </p>
            )}
          </div>
        )}

        {/* Interactive Clickable MCQ Quiz Card Body */}
        {cardType === 'quiz' && (
          <div className="flex flex-col gap-2.5">
            <p className="text-xs font-bold text-zinc-100 leading-snug">
              {data.question}
            </p>
            {data.options && (
              <div className="flex flex-col gap-2 pt-1">
                {data.options.map((opt, i) => {
                  const isCorrect = opt === data.answer;
                  const isSelected = opt === selectedOption;

                  let btnStyle = 'bg-white/5 border-white/15 text-zinc-200 hover:bg-white/10 hover:border-[#10B981]/50';
                  if (isAnswered) {
                    if (isCorrect) {
                      btnStyle = 'bg-[#10B981]/20 border-[#10B981] text-[#10B981] font-bold shadow-[0_0_12px_rgba(16,185,129,0.3)]';
                    } else if (isSelected && !isCorrect) {
                      btnStyle = 'bg-red-500/20 border-red-500 text-red-400 font-bold';
                    }
                  }

                  return (
                    <Button
                      key={i}
                      variant="outline"
                      disabled={isAnswered}
                      onClick={() => handleOptionClick(opt)}
                      className={`w-full justify-start gap-2.5 h-auto py-2.5 px-3 text-[11px] font-mono whitespace-normal text-left transition-all rounded-xl ${btnStyle}`}
                    >
                      <span className="size-5 rounded-full bg-[#EC4899]/20 text-[#EC4899] text-[9px] font-bold flex items-center justify-center shrink-0">
                        {String.fromCharCode(65 + i)}
                      </span>
                      <span className="flex-1">{opt}</span>
                      {isAnswered && isCorrect && <CheckCircle className="size-4 text-[#10B981] shrink-0" />}
                      {isAnswered && isSelected && !isCorrect && <XCircle className="size-4 text-red-400 shrink-0" />}
                    </Button>
                  );
                })}
              </div>
            )}
            {isAnswered && (
              <div className="flex items-center gap-1.5 text-[10px] text-[#10B981] pt-1 font-bold animate-pulse">
                <CheckCircle className="size-3" />
                <span>Response synced with Rishika voice session.</span>
              </div>
            )}
          </div>
        )}
      </motion.div>
    </AnimatePresence>
  );
}
