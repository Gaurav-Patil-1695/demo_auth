import React from 'react';

interface CheckboxProps {
  id: string;
  label: React.ReactNode;
  checked: boolean;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: (e: React.FocusEvent<HTMLInputElement>) => void;
  error?: string;
  disabled?: boolean;
  required?: boolean;
}

function Checkbox({
  id,
  label,
  checked,
  onChange,
  onBlur,
  error,
  disabled = false,
  required = false,
}: CheckboxProps): JSX.Element {
  const errorId = `${id}-error`;

  return (
    <div className={`checkbox${error ? ' checkbox--error' : ''}`}>
      <label className="checkbox__label" htmlFor={id}>
        <input
          id={id}
          type="checkbox"
          className="checkbox__input"
          checked={checked}
          onChange={onChange}
          onBlur={onBlur}
          disabled={disabled}
          required={required}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? errorId : undefined}
        />
        <span className="checkbox__custom" aria-hidden="true" />
        <span className="checkbox__text">
          {label}
          {required && (
            <span className="checkbox__required" aria-hidden="true">
              {' '}*
            </span>
          )}
        </span>
      </label>
      {error && (
        <p id={errorId} className="checkbox__error" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

export default Checkbox;
