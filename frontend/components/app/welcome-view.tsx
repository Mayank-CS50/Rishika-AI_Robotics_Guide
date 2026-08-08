'use client';

import { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
  micError?: string | null;
  onDismissMicError?: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  micError,
  onDismissMicError,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  const [isPreloading, setIsPreloading] = useState(true);
  const [isStarting, setIsStarting] = useState(false);
  const [bootProgress, setBootProgress] = useState(0);

  // Initial mini-preloader boot animation sequence
  useEffect(() => {
    const interval = setInterval(() => {
      setBootProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setTimeout(() => setIsPreloading(false), 200);
          return 100;
        }
        return prev + 25;
      });
    }, 200);

    return () => clearInterval(interval);
  }, []);

  const handleStartClick = () => {
    if (onDismissMicError) onDismissMicError();
    setIsStarting(true);
    onStartCall();
    // Reset starting state after timeout if mic error or canceled
    setTimeout(() => setIsStarting(false), 3500);
  };

  return (
    <motion.div
      ref={ref}
      animate={
        micError
          ? {
              x: [-18, 18, -14, 14, -10, 10, -5, 5, 0],
              rotate: [-1.2, 1.2, -0.8, 0.8, 0],
            }
          : { x: 0, rotate: 0 }
      }
      transition={{ duration: 0.45, ease: 'easeOut' }}
      className="bg-[#080710] min-h-screen text-white font-mono flex flex-col justify-between relative overflow-hidden"
    >
      {/* Background Ambient Glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-gradient-to-tr from-[#EC4899]/15 to-[#10B981]/15 blur-[120px] pointer-events-none rounded-full" />

      {/* Mild Blur & Dimming Backdrop Overlay when Mic Error is Active */}
      <AnimatePresence>
        {micError && (
          <motion.div
            key="mic-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="fixed inset-0 bg-black/30 backdrop-blur-[2px] z-[9990] pointer-events-auto"
            onClick={onDismissMicError}
          />
        )}
      </AnimatePresence>

      {/* Fixed Ultra-Minimal Top-Left Mic Banner (Top Layer z-[9999]) */}
      <AnimatePresence>
        {micError && (
          <motion.div
            key="mic-popover-top"
            initial={{ opacity: 0, y: -12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            className="fixed top-4 left-4 sm:left-8 md:left-12 z-[9999] max-w-[calc(100vw-2rem)] sm:max-w-xs p-4 pl-5 bg-[#0c0a18] border-2 border-red-500/80 shadow-[6px_6px_0px_rgba(239,68,68,0.4)] backdrop-blur-2xl font-mono text-left flex flex-col gap-2.5"
          >
            <div className="flex items-center justify-between gap-1.5 text-[9px] font-bold text-red-400 uppercase tracking-widest border-b border-white/10 pb-1">
              <div className="flex items-center gap-1">
                <span className="animate-bounce">▲</span>
                <span>[ UNBLOCK MIC ABOVE ]</span>
              </div>
              {onDismissMicError && (
                <button
                  onClick={onDismissMicError}
                  className="text-zinc-400 hover:text-white px-1 text-xs"
                  title="Dismiss warning"
                >
                  ✕
                </button>
              )}
            </div>

            <p className="text-[10px] text-zinc-200 leading-snug">
              Click the site settings / mic icon at top-left of address bar ➔ select <strong className="text-white">Allow</strong>.
            </p>

            <div className="flex items-center gap-2">
              <button
                onClick={handleStartClick}
                className="flex-1 py-1.5 px-3 bg-[#10B981]/20 border border-[#10B981] text-[#10B981] text-[9px] font-bold uppercase tracking-wider hover:bg-[#10B981] hover:text-black transition-all flex items-center justify-center gap-1 shadow-[0_0_10px_rgba(16,185,129,0.2)]"
              >
                <span>RETRY ACCESS</span>
                <span>[ ↻ ]</span>
              </button>
              {onDismissMicError && (
                <button
                  onClick={onDismissMicError}
                  className="py-1.5 px-2 bg-white/10 border border-white/30 text-zinc-300 text-[9px] font-bold uppercase hover:bg-white/30 hover:text-white transition-all"
                >
                  DISMISS
                </button>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Mini Preloader Screen */}
      <AnimatePresence>
        {isPreloading && (
          <motion.div
            initial={{ opacity: 1 }}
            exit={{ opacity: 0, scale: 0.98 }}
            transition={{ duration: 0.4, ease: 'easeInOut' }}
            className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-[#080710] p-6"
          >
            <div className="max-w-xs w-full p-6 bg-[#0c0a18]/95 border-2 border-[#EC4899]/50 shadow-[6px_6px_0px_rgba(236,72,153,0.3)] flex flex-col gap-4">
              <div className="flex items-center justify-between text-[10px] text-[#EC4899] tracking-widest uppercase border-b border-white/10 pb-2">
                <span>[ BLUESKY // BOOT ]</span>
                <span className="animate-pulse">SYS_INIT</span>
              </div>

              {/* Animated Frequency Audio Bars */}
              <div className="flex items-center justify-center gap-1.5 h-10 py-1">
                {[0.4, 0.9, 0.6, 1, 0.5, 0.8, 0.3].map((height, i) => (
                  <motion.div
                    key={i}
                    animate={{ height: ['20%', `${height * 100}%`, '20%'] }}
                    transition={{
                      duration: 0.7,
                      repeat: Infinity,
                      delay: i * 0.1,
                      ease: 'easeInOut',
                    }}
                    className="w-1.5 bg-[#EC4899] rounded-full shadow-[0_0_8px_#EC4899]"
                  />
                ))}
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-[10px] text-zinc-400">
                  <span>LOADING RISHIKA_CORE</span>
                  <span className="text-[#10B981] font-bold">{bootProgress}%</span>
                </div>
                {/* Progress bar */}
                <div className="h-1.5 w-full bg-[#080710] border border-white/20 p-0.5 overflow-hidden">
                  <motion.div
                    className="h-full bg-[#EC4899] shadow-[0_0_8px_#EC4899]"
                    initial={{ width: '0%' }}
                    animate={{ width: `${bootProgress}%` }}
                    transition={{ duration: 0.2 }}
                  />
                </div>
              </div>

              <div className="text-[9px] text-zinc-500 uppercase tracking-wider text-center">
                MURF FALCON // DEEPGRAM NOVA-3 // GEMINI
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Landing View Content */}
      <section className="flex flex-col items-center justify-center text-center px-6 min-h-screen py-12 z-10">
        {/* BLUESKY Notebook Card */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: isPreloading ? 0 : 1, y: isPreloading ? 15 : 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="max-w-md w-full p-8 bg-[#0c0a18]/95 border-2 border-white/10 text-white flex flex-col justify-between shadow-[8px_8px_0px_rgba(236,72,153,0.3)] mb-8"
        >
          <div className="flex items-center justify-between text-[9px] text-zinc-500 uppercase tracking-widest text-left mb-4 font-mono">
            <span>[ BLUESKY ROBOTICS VOICE_SYS ]</span>
            <div className="flex items-center gap-2">
              <span className="text-[#10B981] font-bold border border-[#10B981]/50 px-2 py-0.5 bg-[#10B981]/15 shadow-[0_0_8px_rgba(16,185,129,0.2)]">
                STATE: READY
              </span>
            </div>
          </div>

          <h1 className="text-3xl font-bold uppercase leading-none tracking-tight text-white mb-2 font-mono text-left">
            RISHIKA // <br />
            <span className="text-[#EC4899] drop-shadow-[0_0_8px_#EC4899]">LFR ASSISTANT</span>
          </h1>

          <div className="my-6 flex flex-col font-mono text-xl font-bold leading-tight tracking-tight uppercase text-left border-l-4 border-[#EC4899] pl-3">
            <span className="text-zinc-400">SENSORS</span>
            <span className="text-zinc-300">MOTORS</span>
            <span className="text-zinc-200">CHASSIS</span>
            <span className="text-[#EC4899] drop-shadow-[0_0_6px_#EC4899]">DEBUG</span>
          </div>

          <p className="text-[10px] text-zinc-400 text-left leading-relaxed font-mono">
            Voice-powered LFR teaching assistant. Ask about IR sensors, motor drivers, PID tuning, and line follower debugging — in Hindi, English, or Hinglish.
          </p>
        </motion.div>

        {/* Start Button with inline preloader state */}
        <motion.button
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: isPreloading ? 0 : 1, y: isPreloading ? 10 : 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          onClick={handleStartClick}
          disabled={isStarting}
          className="group relative px-8 py-4 uppercase font-bold tracking-widest border-2 border-[#10B981] text-[#10B981] bg-[#10B981]/5 shadow-[6px_6px_0px_rgba(16,185,129,0.25)] hover:shadow-[8px_8px_0px_rgba(16,185,129,0.35)] transition-all duration-150 font-mono text-xs disabled:opacity-80 active:translate-x-[2px] active:translate-y-[2px]"
        >
          {isStarting ? (
            <span className="flex items-center gap-2.5">
              <span className="inline-block size-2 bg-[#10B981] animate-ping" />
              <span>[ INITIALIZING MIC... ]</span>
            </span>
          ) : (
            <span>{startButtonText}</span>
          )}
        </motion.button>
      </section>

      <div className="fixed bottom-5 left-0 flex w-full items-center justify-center pointer-events-none z-10">
        <p className="text-zinc-500 max-w-prose pt-1 text-xs leading-5 font-normal text-pretty md:text-sm font-mono">
          Powered by Murf Falcon TTS — ultra-low latency voice AI
        </p>
      </div>
    </motion.div>
  );
};

