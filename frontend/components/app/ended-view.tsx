'use client';

import { motion } from 'motion/react';

interface EndedViewProps {
  onRestart: () => void;
  onGoHome: () => void;
  ref?: React.Ref<HTMLDivElement>;
}

export const EndedView = ({
  onRestart,
  onGoHome,
  ref,
}: React.ComponentProps<'div'> & EndedViewProps) => {
  return (
    <div
      ref={ref}
      className="bg-[#080710] flex flex-col items-center justify-center min-h-screen px-6 font-mono text-white relative overflow-hidden"
    >
      {/* Soft Ambient Background Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-tr from-[#EC4899]/10 via-[#10B981]/8 to-transparent blur-[140px] pointer-events-none rounded-full" />

      <motion.div
        initial={{ opacity: 0, y: 12, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -12, scale: 0.98 }}
        transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
        className="max-w-md w-full flex flex-col items-center text-center relative z-10 space-y-8"
      >
        {/* Minimalist Status Indicator with Exact Keywords */}
        <div className="space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-red-950/40 border border-red-500/50 text-[#EC4899] font-bold text-xs uppercase tracking-widest shadow-[0_0_10px_rgba(236,72,153,0.3)]">
            <span className="size-2 rounded-full bg-[#EC4899] animate-pulse" />
            <span>STATE: CALL ENDED</span>
          </div>

          <h1 className="text-3xl font-bold uppercase tracking-tight text-white font-mono">
            RISHIKA <span className="text-[#EC4899] drop-shadow-[0_0_12px_rgba(236,72,153,0.4)]">// OFFLINE</span>
          </h1>

          <p className="text-xs text-zinc-300 font-bold max-w-sm mx-auto leading-relaxed">
            The conversation is over. Click below to start again.
          </p>
        </div>

        {/* Minimal Action Controls */}
        <div className="flex flex-col sm:flex-row items-center gap-4 w-full pt-4">
          <button
            onClick={onRestart}
            className="w-full sm:flex-1 py-3.5 px-6 rounded-full border-2 border-[#10B981] text-[#10B981] bg-[#10B981]/10 font-bold uppercase tracking-widest text-xs hover:bg-[#10B981] hover:text-black transition-all duration-200 shadow-[0_0_20px_rgba(16,185,129,0.2)] active:scale-[0.98] flex items-center justify-center gap-2"
          >
            <span>START AGAIN</span>
            <span>[ ↻ ]</span>
          </button>

          <button
            onClick={onGoHome}
            className="w-full sm:w-auto py-3.5 px-6 rounded-full border border-white/20 text-zinc-400 font-bold uppercase tracking-widest text-xs hover:border-white/50 hover:text-white transition-all duration-200 active:scale-[0.98]"
          >
            RETURN HOME
          </button>
        </div>

        <div className="text-[9px] text-zinc-600 uppercase tracking-[0.25em] pt-4">
          BLUESKY // FIREFLY ACADEMY
        </div>
      </motion.div>
    </div>
  );
};
