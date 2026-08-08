'use client';

import { useEffect, useState } from 'react';
import { motion } from 'motion/react';

interface ConnectingViewProps {
  ref?: React.Ref<HTMLDivElement>;
}

export const ConnectingView = ({ ref }: React.ComponentProps<'div'> & ConnectingViewProps) => {
  const [progress, setProgress] = useState(15);
  const [activeStep, setActiveStep] = useState(0);

  const stages = [
    { label: 'ALLOCATING WEBRTC AUDIO PIPELINE', detail: 'OPUS 48KHZ STEREO' },
    { label: 'CONNECTING MURF FALCON TTS ("Anisha")', detail: 'LOW-LATENCY VOICE ENGINE' },
    { label: 'INITIALIZING DEEPGRAM NOVA-3 STT', detail: 'MULTILINGUAL HINGLISH MODEL' },
    { label: 'LOADING VOICE AGENT RISHIKA CORE', detail: 'FIREFLY ACADEMY KNOWLEDGE BASE' },
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + Math.floor(Math.random() * 12) + 8;
      });
    }, 220);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (progress > 25 && activeStep < 1) setActiveStep(1);
    if (progress > 55 && activeStep < 2) setActiveStep(2);
    if (progress > 85 && activeStep < 3) setActiveStep(3);
  }, [progress, activeStep]);

  return (
    <div
      ref={ref}
      className="bg-[#080710] flex flex-col items-center justify-center min-h-screen px-6 font-mono relative overflow-hidden text-white"
    >
      {/* ReactBits Dynamic Background Energy Rings */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        {[1, 2, 3, 4].map((ring) => (
          <motion.div
            key={ring}
            animate={{
              scale: [0.7, 1.9],
              opacity: [0.7, 0],
              rotate: [0, ring % 2 === 0 ? 180 : -180],
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              delay: ring * 0.5,
              ease: 'easeOut',
            }}
            className="absolute rounded-full border border-[#10B981]/30 w-[340px] h-[340px]"
            style={{
              borderColor: ring % 2 === 0 ? 'rgba(236,72,153,0.35)' : 'rgba(16,185,129,0.35)',
            }}
          />
        ))}
      </div>

      {/* Main Connection Container */}
      <motion.div
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 1.04 }}
        transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
        className="max-w-md w-full p-8 bg-[#0c0a18]/95 border-2 border-white/10 shadow-[12px_12px_0px_rgba(236,72,153,0.3)] relative z-10 flex flex-col items-center gap-6"
      >
        {/* Header Badge */}
        <div className="flex items-center justify-between w-full text-[9px] text-[#EC4899] tracking-widest uppercase border-b border-white/10 pb-2">
          <span>[ VOICE_AGENT_BOOT // TRANSITION ]</span>
          <span className="text-[#10B981] font-bold animate-pulse">{progress}% LOADED</span>
        </div>

        {/* ReactBits Central Core Node */}
        <div className="relative flex items-center justify-center size-24 my-2">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 6, repeat: Infinity, ease: 'linear' }}
            className="absolute inset-0 rounded-full border-2 border-dashed border-[#EC4899]/70 shadow-[0_0_20px_rgba(236,72,153,0.4)]"
          />
          <motion.div
            animate={{ rotate: -360 }}
            transition={{ duration: 9, repeat: Infinity, ease: 'linear' }}
            className="absolute inset-2 rounded-full border border-dotted border-[#10B981]/70"
          />

          {/* Central Audio Equalizer Bars */}
          <div className="flex items-end justify-center gap-1 h-8 z-10">
            {[0.4, 0.8, 0.5, 1, 0.6, 0.9, 0.3].map((h, i) => (
              <motion.span
                key={i}
                animate={{ scaleY: [h, 1.2, 0.2, h] }}
                transition={{
                  duration: 0.8,
                  repeat: Infinity,
                  delay: i * 0.1,
                  ease: 'easeInOut',
                }}
                className="w-1 bg-[#10B981] rounded-full shadow-[0_0_8px_#10B981] origin-bottom"
                style={{ height: '100%' }}
              />
            ))}
          </div>
        </div>

        {/* Title & Exact Keyword State */}
        <div className="space-y-1.5 text-center w-full">
          <div className="inline-block px-3 py-1 bg-[#10B981]/15 border border-[#10B981] text-[#10B981] font-bold text-xs uppercase tracking-widest shadow-[0_0_10px_rgba(16,185,129,0.3)]">
            STATE: CONNECTING
          </div>
          <h2 className="text-xl font-bold uppercase tracking-tight text-white font-mono pt-1">
            AGENT IS JOINING THE CALL
          </h2>
          <p className="text-[10px] text-zinc-300 font-bold">
            Please wait while voice agent Rishika initializes...
          </p>
        </div>

        {/* Progress Bar */}
        <div className="w-full space-y-1">
          <div className="h-2 w-full bg-[#080710] border border-white/20 p-0.5 overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-[#EC4899] to-[#10B981] shadow-[0_0_10px_#10B981]"
              style={{ width: `${Math.min(progress, 100)}%` }}
            />
          </div>
        </div>

        {/* Live Stage Log */}
        <div className="w-full bg-[#080710] p-4 border border-white/10 text-left space-y-2 font-mono text-[10px]">
          {stages.map((stage, idx) => {
            const isDone = idx < activeStep || progress >= 100;
            const isCurrent = idx === activeStep && progress < 100;

            return (
              <div
                key={stage.label}
                className="flex items-start justify-between gap-2 border-b border-white/5 pb-1.5 last:border-0 last:pb-0"
              >
                <div className="space-y-0.5">
                  <div
                    className={
                      isDone
                        ? 'text-[#10B981] font-bold'
                        : isCurrent
                        ? 'text-[#EC4899] font-bold animate-pulse'
                        : 'text-zinc-600'
                    }
                  >
                    [{`0${idx + 1}`}] {stage.label}
                  </div>
                  <div className="text-[8px] text-zinc-500">{stage.detail}</div>
                </div>

                <span
                  className={`text-[9px] font-bold ${
                    isDone
                      ? 'text-[#10B981]'
                      : isCurrent
                      ? 'text-[#EC4899]'
                      : 'text-zinc-600'
                  }`}
                >
                  {isDone ? '[ READY ]' : isCurrent ? '[ LOADING ]' : '[ PENDING ]'}
                </span>
              </div>
            );
          })}
        </div>

        <div className="text-[9px] text-zinc-500 uppercase tracking-widest text-center">
          BLUESKY // FIREFLY ACADEMY VOICE_SYS
        </div>
      </motion.div>
    </div>
  );
};
