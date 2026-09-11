import React, { useState, useId } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { register } from '../../../api/auth';

interface FormValues {
  fullName: string;
  email: string;
  password: string;
  confirmPassword: string;
  acceptTerms: boolean;
}

interface FormErrors {
  fullName?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
  acceptTerms?: string;
}

function getPasswordStrength(password: string): number {
  let score = 0;
  if (password.length >= 8) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[a-z]/.test(password)) score++;
  if (/\d/.test(password)) score++;
  return score;
}

function validateForm(values: FormValues): FormErrors {
  const errors: FormErrors = {};

  if (!values.fullName || values.fullName.trim().length < 1) {
    errors.fullName = 'Full name is required.';
  } else if (values.fullName.length > 120) {
    errors.fullName = 'Full name is required.';
  }

  if (!values.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email)) {
    errors.email = 'Enter a valid email address.';
  }

  if (!values.password || values.password.length < 8) {
    errors.password = 'Password must be at least 8 characters.';
  } else if (!/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/.test(values.password)) {
    errors.password = 'Password must be at least 8 characters.';
  }

  if (!values.confirmPassword || values.confirmPassword !== values.password) {
    errors.confirmPassword = 'Passwords do not match.';
  }

  if (!values.acceptTerms) {
    errors.acceptTerms = 'You must accept the Terms to continue.';
  }

  return errors;
}

const strengthLabels = ['', 'Weak', 'Fair', 'Good', 'Strong'];
const strengthColors = [
  'transparent',
  'var(--color-error)',
  'var(--color-warning)',
  'var(--color-info)',
  'var(--color-success)',
];

export default function RegisterPage(): JSX.Element {
  const navigate = useNavigate();
  const idPrefix = useId();

  const [values, setValues] = useState<FormValues>({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
    acceptTerms: false,
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [serverError, setServerError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const passwordStrength = getPasswordStrength(values.password);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>): void {
    const { name, value, type, checked } = e.target;
    setValues((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
    setErrors((prev) => ({ ...prev, [name]: undefined }));
    setServerError(null);
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>): Promise<void> {
    e.preventDefault();
    const validationErrors = validateForm(values);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setIsSubmitting(true);
    setServerError(null);

    try {
      await register({
        fullName: values.fullName,
        email: values.email,
        password: values.password,
        confirmPassword: values.confirmPassword,
      });
      navigate('/login', { replace: true });
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : 'Registration failed. Please try again.';
      if (message.toLowerCase().includes('email')) {
        setErrors((prev) => ({ ...prev, email: 'That email is already registered.' }));
      } else {
        setServerError(message);
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  const fullNameId = `${idPrefix}-full-name`;
  const fullNameErrId = `${idPrefix}-full-name-err`;
  const emailId = `${idPrefix}-email`;
  const emailErrId = `${idPrefix}-email-err`;
  const passwordId = `${idPrefix}-password`;
  const passwordErrId = `${idPrefix}-password-err`;
  const confirmPasswordId = `${idPrefix}-confirm-password`;
  const confirmPasswordErrId = `${idPrefix}-confirm-password-err`;
  const acceptTermsId = `${idPrefix}-accept-terms`;
  const acceptTermsErrId = `${idPrefix}-accept-terms-err`;
  const serverErrId = `${idPrefix}-server-err`;

  return (
    <>
      <style>{`
        :root {
          --color-accent-primary: #4f46e5;
          --color-accent-primary-hover: #4338ca;
          --color-accent-primary-active: #3730a3;
          --color-accent-disabled: #c7d2fe;
          --color-bg-app: #f1f5f9;
          --color-border: #E2E8F0;
          --color-border-strong: #CBD5E1;
          --color-error: #DC2626;
          --color-focus-ring: #818cf8;
          --color-info: #2563EB;
          --color-link: #4f46e5;
          --color-muted-surface: #f8fafc;
          --color-success: #16A34A;
          --color-surface: #FFFFFF;
          --color-text-muted: #94A3B8;
          --color-text-primary: #0F172A;
          --color-text-secondary: #475569;
          --color-warning: #D97706;
          --elevation-card: 0 12px 32px rgba(15,23,42,0.12);
          --elevation-focus: 0 0 0 3px rgba(129,140,248,0.45);
          --font-family-base: Inter, 'Segoe UI', system-ui, -apple-system, sans-serif;
          --radius-card: 16px;
          --radius-input: 8px;
          --radius-button: 8px;
          --space-xs: 4px;
          --space-sm: 8px;
          --space-md: 16px;
          --space-lg: 24px;
          --space-xl: 32px;
          --space-2xl: 48px;
        }

        .register-page {
          min-height: 100vh;
          background-color: var(--color-bg-app);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: var(--space-lg);
          font-family: var(--font-family-base);
          color: var(--color-text-primary);
        }

        .auth-brand {
          margin-bottom: var(--space-lg);
          text-align: center;
        }

        .auth-brand__logo {
          font-size: 30px;
          font-weight: 700;
          line-height: 1.2;
          color: var(--color-accent-primary);
        }

        .auth-brand__tagline {
          font-size: 14px;
          font-weight: 500;
          color: var(--color-text-secondary);
          margin-top: var(--space-xs);
        }

        .auth-card {
          background: var(--color-surface);
          border-radius: var(--radius-card);
          box-shadow: var(--elevation-card);
          padding: var(--space-xl);
          width: 100%;
          max-width: 420px;
        }

        .auth-card__title {
          font-size: 30px;
          font-weight: 700;
          line-height: 1.2;
          color: var(--color-text-primary);
          margin: 0 0 var(--space-xs) 0;
        }

        .auth-card__subtitle {
          font-size: 14px;
          font-weight: 500;
          color: var(--color-text-secondary);
          margin: 0 0 var(--space-xl) 0;
        }

        .auth-card__form {
          display: flex;
          flex-direction: column;
          gap: var(--space-md);
        }

        .auth-card__field {
          display: flex;
          flex-direction: column;
          gap: var(--space-xs);
        }

        .field__label {
          font-size: 14px;
          font-weight: 500;
          color: var(--color-text-primary);
        }

        .field__input-wrapper {
          position: relative;
          display: flex;
          align-items: center;
        }

        .field__input {
          width: 100%;
          padding: var(--space-sm) var(--space-md);
          font-size: 16px;
          font-family: var(--font-family-base);
          color: var(--color-text-primary);
          background: var(--color-surface);
          border: 1.5px solid var(--color-border-strong);
          border-radius: var(--radius-input);
          outline: none;
          box-sizing: border-box;
          transition: border-color 0.15s, box-shadow 0.15s;
        }

        .field__input:focus {
          border-color: var(--color-accent-primary);
          box-shadow: var(--elevation-focus);
        }

        .field__input--error {
          border-color: var(--color-error);
        }

        .field__input--with-toggle {
          padding-right: 44px;
        }

        .field__toggle-btn {
          position: absolute;
          right: var(--space-sm);
          background: none;
          border: none;
          cursor: pointer;
          padding: var(--space-xs);
          color: var(--color-text-muted);
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: var(--radius-button);
          transition: color 0.15s;
        }

        .field__toggle-btn:hover {
          color: var(--color-text-secondary);
        }

        .field__toggle-btn:focus-visible {
          outline: 2px solid var(--color-focus-ring);
          outline-offset: 2px;
        }

        .field__error {
          font-size: 12px;
          color: var(--color-error);
          line-height: 1.5;
          margin: 0;
        }

        .field--error .field__label {
          color: var(--color-error);
        }

        .password-strength {
          display: flex;
          flex-direction: column;
          gap: var(--space-xs);
          margin-top: var(--space-xs);
        }

        .password-strength__bars {
          display: flex;
          gap: var(--space-xs);
        }

        .password-strength__bar {
          flex: 1;
          height: 4px;
          border-radius: 9999px;
          background: var(--color-border);
          transition: background 0.2s;
        }

        .password-strength__label {
          font-size: 12px;
          color: var(--color-text-muted);
          line-height: 1.5;
        }

        .checkbox-field {
          display: flex;
          align-items: flex-start;
          gap: var(--space-sm);
        }

        .checkbox-field__input {
          margin-top: 2px;
          width: 16px;
          height: 16px;
          accent-color: var(--color-accent-primary);
          cursor: pointer;
          flex-shrink: 0;
        }

        .checkbox-field__label {
          font-size: 14px;
          font-weight: 500;
          color: var(--color-text-secondary);
          cursor: pointer;
          line-height: 1.5;
        }

        .checkbox-field__link {
          color: var(--color-link);
          text-decoration: none;
        }

        .checkbox-field__link:hover {
          text-decoration: underline;
        }

        .server-error {
          padding: var(--space-sm) var(--space-md);
          background: #fef2f2;
          border: 1px solid var(--color-error);
          border-radius: var(--radius-input);
          font-size: 14px;
          color: var(--color-error);
          line-height: 1.5;
          margin: 0;
        }

        .auth-card__submit {
          width: 100%;
          padding: var(--space-sm) var(--space-md);
          font-size: 16px;
          font-weight: 600;
          font-family: var(--font-family-base);
          color: #ffffff;
          background-color: var(--color-accent-primary);
          border: none;
          border-radius: var(--radius-button);
          cursor: pointer;
          transition: background-color 0.15s;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: var(--space-sm);
          margin-top: var(--space-sm);
        }

        .auth-card__submit:hover:not(:disabled) {
          background-color: var(--color-accent-primary-hover);
        }

        .auth-card__submit:active:not(:disabled) {
          background-color: var(--color-accent-primary-active);
        }

        .auth-card__submit:disabled {
          background-color: var(--color-accent-disabled);
          cursor: not-allowed;
        }

        .auth-card__submit:focus-visible {
          outline: 2px solid var(--color-focus-ring);
          outline-offset: 2px;
        }

        .spinner {
          width: 16px;
          height: 16px;
          border: 2px solid rgba(255, 255, 255, 0.4);
          border-top-color: #ffffff;
          border-radius: 50%;
          animation: spin 0.7s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .auth-card__footer {
          margin: var(--space-lg) 0 0 0;
          text-align: center;
          font-size: 14px;
          font-weight: 500;
          color: var(--color-text-secondary);
        }

        .link {
          color: var(--color-link);
          text-decoration: none;
          font-weight: 500;
        }

        .link:hover {
          text-decoration: underline;
        }
      `}</style>

      <div className="register-page">
        <div className="auth-brand">
          <div className="auth-brand__logo">auth-starter</div>
          <p className="auth-brand__tagline">Secure authentication, out of the box.</p>
        </div>

        <div className="auth-card">
          <h1 className="auth-card__title">Create account</h1>
          <p className="auth-card__subtitle">Sign up to get started.</p>

          {serverError && (
            <div aria-live="polite">
              <p className="server-error" id={serverErrId} role="alert">
                {serverError}
              </p>
            </div>
          )}

          <form className="auth-card__form" onSubmit={handleSubmit} noValidate>
            {/* Full Name */}
            <div className={`auth-card__field${errors.fullName ? ' field--error' : ''}`}>
              <label className="field__label" htmlFor={fullNameId}>
                Full name
              </label>
              <div className="field__input-wrapper">
                <input
                  id={fullNameId}
                  className={`field__input${errors.fullName ? ' field__input--error' : ''}`}
                  type="text"
                  name="fullName"
                  value={values.fullName}
                  onChange={handleChange}
                  autoComplete="name"
                  aria-describedby={errors.fullName ? fullNameErrId : undefined}
                  aria-invalid={!!errors.fullName}
                  disabled={isSubmitting}
                />
              </div>
              {errors.fullName && (
                <p className="field__error" id={fullNameErrId}>
                  {errors.fullName}
                </p>
              )}
            </div>

            {/* Email */}
            <div className={`auth-card__field${errors.email ? ' field--error' : ''}`}>
              <label className="field__label" htmlFor={emailId}>
                Email address
              </label>
              <div className="field__input-wrapper">
                <input
                  id={emailId}
                  className={`field__input${errors.email ? ' field__input--error' : ''}`}
                  type="email"
                  name="email"
                  value={values.email}
                  onChange={handleChange}
                  autoComplete="email"
                  aria-describedby={errors.email ? emailErrId : undefined}
                  aria-invalid={!!errors.email}
                  disabled={isSubmitting}
                />
              </div>
              {errors.email && (
                <p className="field__error" id={emailErrId}>
                  {errors.email}
                </p>
              )}
            </div>

            {/* Password */}
            <div className={`auth-card__field${errors.password ? ' field--error' : ''}`}>
              <label className="field__label" htmlFor={passwordId}>
                Password
              </label>
              <div className="field__input-wrapper">
                <input
                  id={passwordId}
                  className={`field__input field__input--with-toggle${errors.password ? ' field__input--error' : ''}`}
                  type={showPassword ? 'text' : 'password'}
                  name="password"
                  value={values.password}
                  onChange={handleChange}
                  autoComplete="new-password"
                  aria-describedby={errors.password ? passwordErrId : undefined}
                  aria-invalid={!!errors.password}
                  disabled={isSubmitting}
                />
                <button
                  type="button"
                  className="field__toggle-btn"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  onClick={() => setShowPassword((v) => !v)}
                  tabIndex={0}
                >
                  {showPassword ? (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
                      <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
                      <line x1="1" y1="1" x2="23" y2="23" />
                    </svg>
                  ) : (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                  )}
                </button>
              </div>
              {values.password.length > 0 && (
                <div className="password-strength">
                  <div className="password-strength__bars" role="presentation">
                    {[1, 2, 3, 4].map((level) => (
                      <div
                        key={level}
                        className="password-strength__bar"
                        style={{
                          background:
                            passwordStrength >= level
                              ? strengthColors[passwordStrength]
                              : 'var(--color-border)',
                        }}
                      />
                    ))}
                  </div>
                  <span className="password-strength__label">
                    {passwordStrength > 0 ? strengthLabels[passwordStrength] : ''}
                  </span>
                </div>
              )}
              {errors.password && (
                <p className="field__error" id={passwordErrId}>
                  {errors.password}
                </p>
              )}
            </div>

            {/* Confirm Password */}
            <div className={`auth-card__field${errors.confirmPassword ? ' field--error' : ''}`}>
              <label className="field__label" htmlFor={confirmPasswordId}>
                Confirm password
              </label>
              <div className="field__input-wrapper">
                <input
                  id={confirmPasswordId}
                  className={`field__input field__input--with-toggle${errors.confirmPassword ? ' field__input--error' : ''}`}
                  type={showConfirmPassword ? 'text' : 'password'}
                  name="confirmPassword"
                  value={values.confirmPassword}
                  onChange={handleChange}
                  autoComplete="new-password"
                  aria-describedby={errors.confirmPassword ? confirmPasswordErrId : undefined}
                  aria-invalid={!!errors.confirmPassword}
                  disabled={isSubmitting}
                />
                <button
                  type="button"
                  className="field__toggle-btn"
                  aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                  onClick={() => setShowConfirmPassword((v) => !v)}
                  tabIndex={0}
                >
                  {showConfirmPassword ? (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
                      <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
                      <line x1="1" y1="1" x2="23" y2="23" />
                    </svg>
                  ) : (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                  )}
                </button>
              </div>
              {errors.confirmPassword && (
                <p className="field__error" id={confirmPasswordErrId}>
                  {errors.confirmPassword}
                </p>
              )}
            </div>

            {/* Accept Terms */}
            <div className={`auth-card__field${errors.acceptTerms ? ' field--error' : ''}`}>
              <div className="checkbox-field">
                <input
                  id={acceptTermsId}
                  className="checkbox-field__input"
                  type="checkbox"
                  name="acceptTerms"
                  checked={values.acceptTerms}
                  onChange={handleChange}
                  aria-describedby={errors.acceptTerms ? acceptTermsErrId : undefined}
                  aria-invalid={!!errors.acceptTerms}
                  disabled={isSubmitting}
                />
                <label className="checkbox-field__label" htmlFor={acceptTermsId}>
                  I agree to the{' '}
                  <a className="checkbox-field__link" href="/terms" target="_blank" rel="noopener noreferrer">
                    Terms of Service
                  </a>{' '}
                  and{' '}
                  <a className="checkbox-field__link" href="/privacy" target="_blank" rel="noopener noreferrer">
                    Privacy Policy
                  </a>
                </label>
              </div>
              {errors.acceptTerms && (
                <p className="field__error" id={acceptTermsErrId}>
                  {errors.acceptTerms}
                </p>
              )}
            </div>

            <button
              type="submit"
              className="auth-card__submit"
              disabled={isSubmitting}
              aria-busy={isSubmitting}
            >
              {isSubmitting && <span className="spinner" aria-hidden="true" />}
              {isSubmitting ? 'Creating account…' : 'Create account'}
            </button>
          </form>

          <p className="auth-card__footer">
            Already have an account?{' '}
            <Link className="link" to="/login">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </>
  );
}
