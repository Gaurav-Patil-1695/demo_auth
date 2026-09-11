import React from 'react';

function Branding(): JSX.Element {
  return (
    <div className="branding">
      <div className="branding__logo" aria-hidden="true">
        <svg
          width="48"
          height="48"
          viewBox="0 0 48 48"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="branding__logo-icon"
        >
          <rect width="48" height="48" rx="12" fill="var(--color-accent-primary)" />
          <path
            d="M24 12C18.477 12 14 16.477 14 22C14 25.728 15.973 28.998 18.938 30.938L18 36L23.062 33.562C23.364 33.604 23.679 33.625 24 33.625C29.523 33.625 34 29.148 34 23.625C34 18.102 29.523 12 24 12Z"
            fill="white"
          />
        </svg>
      </div>
      <span className="branding__wordmark">AuthStarter</span>
    </div>
  );
}

export default Branding;
