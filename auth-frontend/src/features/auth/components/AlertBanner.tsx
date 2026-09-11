import React from 'react';

interface AlertBannerProps {
  readonly type: 'success' | 'error';
  readonly message: string;
}

function AlertBanner({ type, message }: AlertBannerProps): JSX.Element | null {
  if (!message) {
    return null;
  }

  if (type === 'error') {
    return (
      <div
        className={`alert-banner alert-banner--${type}`}
        role="alert"
        aria-live="polite"
        aria-atomic="true"
      >
        <span className="alert-banner__icon" aria-hidden="true">
          <svg
            width="18"
            height="18"
            viewBox="0 0 18 18"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            focusable="false"
          >
            <circle cx="9" cy="9" r="8" stroke="currentColor" strokeWidth="1.5" />
            <path
              d="M9 5.5V9.5"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
            <circle cx="9" cy="12" r="0.75" fill="currentColor" />
          </svg>
        </span>
        <span className="alert-banner__message">{message}</span>
      </div>
    );
  }

  return (
    <output
      className={`alert-banner alert-banner--${type}`}
      aria-live="polite"
      aria-atomic="true"
    >
      <span className="alert-banner__icon" aria-hidden="true">
        <svg
          width="18"
          height="18"
          viewBox="0 0 18 18"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          focusable="false"
        >
          <circle cx="9" cy="9" r="8" stroke="currentColor" strokeWidth="1.5" />
          <path
            d="M5.5 9L7.5 11L12.5 7"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </span>
      <span className="alert-banner__message">{message}</span>
    </output>
  );
}

export default AlertBanner;
