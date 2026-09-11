import React from 'react';

interface Rule {
  readonly key: string;
  readonly label: string;
  readonly test: (password: string) => boolean;
}

const RULES: Rule[] = [
  {
    key: 'length',
    label: 'At least 8 characters',
    test: (password) => password.length >= 8,
  },
  {
    key: 'uppercase',
    label: 'At least one uppercase letter',
    test: (password) => /[A-Z]/.test(password),
  },
  {
    key: 'lowercase',
    label: 'At least one lowercase letter',
    test: (password) => /[a-z]/.test(password),
  },
  {
    key: 'number',
    label: 'At least one number',
    test: (password) => /[0-9]/.test(password),
  },
];

interface PasswordStrengthMeterProps {
  readonly password: string;
}

function PasswordStrengthMeter({ password }: PasswordStrengthMeterProps): JSX.Element {
  const results = RULES.map((rule) => ({
    key: rule.key,
    label: rule.label,
    passed: rule.test(password),
  }));

  const passedCount = results.filter((r) => r.passed).length;

  function getStrengthLabel(): string {
    if (passedCount === 0) return 'None';
    if (passedCount === 1) return 'Weak';
    if (passedCount === 2) return 'Fair';
    if (passedCount === 3) return 'Good';
    return 'Strong';
  }

  function getStrengthModifier(): string {
    if (passedCount === 0) return 'none';
    if (passedCount === 1) return 'weak';
    if (passedCount === 2) return 'fair';
    if (passedCount === 3) return 'good';
    return 'strong';
  }

  const strengthLabel = getStrengthLabel();
  const strengthModifier = getStrengthModifier();

  return (
    <div className="password-strength" aria-label="Password strength">
      <div
        className="password-strength__bars"
        role="img"
        aria-label={`Password strength: ${strengthLabel}`}
      >
        {RULES.map((rule, index) => (
          <div
            key={rule.key}
            className={[
              'password-strength__bar',
              index < passedCount
                ? `password-strength__bar--${strengthModifier}`
                : 'password-strength__bar--empty',
            ].join(' ')}
          />
        ))}
      </div>
      {password.length > 0 && (
        <span className={`password-strength__label password-strength__label--${strengthModifier}`}>
          {strengthLabel}
        </span>
      )}
      <ul className="password-strength__checklist" aria-label="Password requirements">
        {results.map((result) => (
          <li
            key={result.key}
            className={[
              'password-strength__rule',
              result.passed
                ? 'password-strength__rule--passed'
                : 'password-strength__rule--failed',
            ].join(' ')}
          >
            <span
              className="password-strength__rule-icon"
              aria-hidden="true"
            >
              {result.passed ? '✓' : '○'}
            </span>
            <span className="password-strength__rule-text">{result.label}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default PasswordStrengthMeter;
