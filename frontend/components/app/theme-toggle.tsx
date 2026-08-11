'use client';

import { useEffect, useState } from 'react';
import { useTheme } from 'next-themes';
import { MonitorIcon, MoonIcon, SunIcon } from '@phosphor-icons/react';
import { cn } from '@/lib/shadcn/utils';

interface ThemeToggleProps {
  className?: string;
}

export function ThemeToggle({ className }: ThemeToggleProps) {
  const [mounted, setMounted] = useState(false);
  const { theme, setTheme } = useTheme();

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div
      className={cn(
        'text-foreground bg-background flex w-full flex-row justify-end divide-x overflow-hidden rounded-full border',
        className
      )}
    >
      <span className="sr-only">Color scheme toggle</span>
      <button type="button" onClick={() => setTheme('dark')} className="cursor-pointer p-1 pl-1.5">
        <span className="sr-only">Enable dark color scheme</span>
        <MoonIcon
          suppressHydrationWarning
          size={16}
          weight="bold"
          className={cn((!mounted || theme !== 'dark') && 'opacity-25')}
        />
      </button>
      <button
        type="button"
        onClick={() => setTheme('light')}
        className="cursor-pointer px-1.5 py-1"
      >
        <span className="sr-only">Enable light color scheme</span>
        <SunIcon
          suppressHydrationWarning
          size={16}
          weight="bold"
          className={cn((!mounted || theme !== 'light') && 'opacity-25')}
        />
      </button>
      <button
        type="button"
        onClick={() => setTheme('system')}
        className="cursor-pointer p-1 pr-1.5"
      >
        <span className="sr-only">Enable system color scheme</span>
        <MonitorIcon
          suppressHydrationWarning
          size={16}
          weight="bold"
          className={cn((!mounted || theme !== 'system') && 'opacity-25')}
        />
      </button>
    </div>
  );
}
