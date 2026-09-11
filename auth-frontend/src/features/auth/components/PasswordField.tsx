import React, { useState } from 'react';

interface PasswordFieldProps {
  readonly id: string;
  readonly label: string;
  readonly value: string;
  readonly onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  readonly onBlur?: (e: React.FocusEvent<HTMLInputElement>) => void;
  readonly error?: string;
  readonly hint?: string;
  readonly autoComplete?: string;
  readonly placeholder?: string;
  readonly disabled?: boolean;
  readonly required?: boolean;
}

function PasswordField({
  id,
  label,
  value,
  onChange,
  onBlur,
  error,
  hint,
  autoComplete,
  placeholder,
  disabled = false,
  required = false,
}: PasswordFieldProps): JSX.Element {
  const [isVisible, setIsVisible] = useState(false);

  const errorId = `${id}-error`;
  const hintId = `${id}-hint`;

  const describedBy = [
    error ? errorId : null,
    hint ? hintId : null,
  ]
    .filter(Boolean)
    .join(' ');

  function handleToggleVisibility(): void {
    setIsVisible((prev) => !prev);
  }

  return (
    <div className={`field${error ? ' field--error' : ''}`}>
      <label className="field__label" htmlFor={id}>
        {label}
        {required && (
          <span className="field__required" aria-hidden="true">
            {' '}*
          </span>
        )}
      </label>
      <div className="field__input-wrapper">
        <input
          id={id}
          type={isVisible ? 'text' : 'password'}
          className="field__input field__input--password"
          value={value}
          onChange={onChange}
          onBlur={onBlur}
          autoComplete={autoComplete}
          placeholder={placeholder}
          disabled={disabled}
          required={required}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={describedBy || undefined}
        />
        <button
          type="button"
          className="field__password-toggle"
          aria-label={isVisible ? 'Hide password' : 'Show password'}
          onClick={handleToggleVisibility}
          disabled={disabled}
          tabIndex={0}
        >
          {isVisible ? (
            <svg
              width="20"
              height="20"
              viewBox="0 0 20 20"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              aria-hidden="true"
              focusable="false"
            >
              <path
                d="M2.5 10C2.5 10 5 4.375 10 4.375C15 4.375 17.5 10 17.5 10C17.5 10 15 15.625 10 15.625C5 15.625 2.5 10 2.5 10Z"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <circle
                cx="10"
                cy="10"
                r="2.5"
                stroke="currentColor"
                strokeWidth="1.5"
              />
              <line
                x1="3"
                y1="3"
                x2="17"
                y2="17"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            </svg>
          ) : (
            <svg
              width="20"
              height="20"
              viewBox="0 0 20 20"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              aria-hidden="true"
              focusable="false"
            >
              <path
                d="M2.5 10C2.5 10 5 4.375 10 4.375C15 4.375 17.5 10 17.5 10C17.5 10 15 15.625 10 15.625C5 15.625 2.5 10 2.5 10Z"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <circle
                cx="10"
                cy="10"
                r="2.5"
                stroke="currentColor"
                strokeWidth="1.5"
              />
            </svg>
          )}
        </button>
      </div>
      {hint && !error && (
        <p id={hintId} className="field__hint">
          {hint}
        </p>
      )}
      {error && (
        <p id={errorId} className="field__error" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

export default PasswordField;
