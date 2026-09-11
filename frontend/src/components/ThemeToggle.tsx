import React from 'react';
import { useTheme } from '../hooks/useTheme';

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <button
      type='button'
      onClick={toggleTheme}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      aria-pressed={isDark}
      className='theme-toggle'
    >
      <span className='theme-toggle__icon' aria-hidden='true'>
        {isDark ? '☀️' : '🌙'}
      </span>
      <span className='theme-toggle__label'>
        {isDark ? 'Light mode' : 'Dark mode'}
      </span>
    </button>
  );
}
