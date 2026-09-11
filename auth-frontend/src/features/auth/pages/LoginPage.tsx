import React, { useState, useId } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { login } from '../../../api/auth';

interface LoginFormState {
  email: string;
  password: string;
  rememberMe: boolean;
}

interface LoginFormErrors {
  email?: string;
  password?: string;
  form?: string;
}

function validateLoginForm(values: LoginFormState): LoginFormErrors {
  const errors: LoginFormErrors = {};

  if (!values.email || values.email.trim() === '') {
    errors.email = 'Enter a valid email address.';
  } else {
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(values.email.trim())) {
      errors.email = 'Enter a valid email address.';
    }
  }

  if (!values.password || values.password.length < 1) {
    errors.password = 'Password is required.';
  }

  return errors;
}

export default function LoginPage(): React.ReactElement {
  const navigate = useNavigate();
  const emailId = useId();
  const passwordId = useId();
  const emailErrorId = useId();
  const passwordErrorId = useId();
  const formErrorId = useId();

  const [values, setValues] = useState<LoginFormState>({
    email: '',
    password: '',
    rememberMe: false,
  });
  const [errors, setErrors] = useState<LoginFormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  function handleEmailChange(e: React.ChangeEvent<HTMLInputElement>): void {
    setValues((prev) => ({ ...prev, email: e.target.value }));
    if (errors.email) {
      setErrors((prev) => ({ ...prev, email: undefined }));
    }
  }

  function handlePasswordChange(e: React.ChangeEvent<HTMLInputElement>): void {
    setValues((prev) => ({ ...prev, password: e.target.value }));
    if (errors.password) {
      setErrors((prev) => ({ ...prev, password: undefined }));
    }
  }

  function handleRememberMeChange(e: React.ChangeEvent<HTMLInputElement>): void {
    setValues((prev) => ({ ...prev, rememberMe: e.target.checked }));
  }

  function handleTogglePassword(): void {
    setShowPassword((prev) => !prev);
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>): Promise<void> {
    e.preventDefault();

    const validationErrors = validateLoginForm(values);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setIsSubmitting(true);
    setErrors({});

    try {
      await login({
        email: values.email.trim(),
        password: values.password,
        rememberMe: values.rememberMe,
      });
      navigate('/');
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Invalid email or password.';
      setErrors({ form: message });
    } finally {
      setIsSubmitting(false);
    }
  }

  const hasFormError = Boolean(errors.form);

  return (
    <>
      <style>{`
        :root {
          --color-accent-disabled: #c7d2fe;
          --color-accent-primary: #4f46e5;
          --color-accent-primary-active: #3730a3;
          --color-accent-primary-hover: #4338ca;
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
          --elevation-1: 0 1px 2px rgba(15,23,42,0.06);
          --elevation-2: 0 4px 12px rgba(15,23,42,0.08);
          --elevation-card: 0 12px 32px rgba(15,23,42,0.12);
          --elevation-focus: 0 0 0 3px rgba(129,140,248,0.45);
          --family-base: Inter, 'Segoe UI', system-ui, -apple-system, sans-serif;
          --radius-button: 8px;
          --radius-card: 16px;
          --radius-full: 9999px;
          --radius-input: 8px;
          --radius-sm: 4px;
          --space-2xl: 48px;
          --space-lg: 24px;
          --space-md: 16px;
          --space-sm: 8px;
          --space-xl: 32px;
          --space-xs: 4px;
        }

        *,
        *::before,
        *::after {
          box-sizing: border-box;
        }

        .login-page {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          background-color: var(--color-bg-app);
          font-family: var(--family-base);
          padding: var(--space-md);
        }

        .login-page__branding {
          margin-bottom: var(--space-lg);
          text-align: center;
        }

        .login-page__brand-name {
          font-size: 30px;
          font-weight: 700;
          line-height: 1.2;
          color: var(--color-accent-primary);
          margin: 0;
        }

        .auth-card {
          background-color: var(--color-surface);
          border-radius: var(--radius-card);
          box-shadow: var(--elevation-card);
          padding: var(--space-2xl);
          width: 100%;
          max-width: 440px;
        }

        .auth-card__title {
          font-size: 30px;
          font-weight: 700;
          line-height: 1.2;
          color: var(--color-text-primary);
          margin: 0 0 var(--space-xl) 0;
          text-align: center;
        }

        .auth-card__banner {
          border-radius: var(--radius-sm);
          padding: var(--space-sm) var(--space-md);
          margin-bottom: var(--space-md);
          font-size: 14px;
          font-weight: 500;
          line-height: 1.5;
        }

        .auth-card__banner--error {
          background-color: #fef2f2;
          color: var(--color-error);
          border: 1px solid #fecaca;
        }

        .auth-card__field {
          margin-bottom: var(--space-md);
        }

        .auth-card__label {
          display: block;
          font-size: 14px;
          font-weight: 500;
          line-height: 1.5;
          color: var(--color-text-secondary);
          margin-bottom: var(--space-xs);
        }

        .auth-card__input-wrapper {
          position: relative;
          display: flex;
          align-items: center;
        }

        .auth-card__input {
          width: 100%;
          height: 44px;
          padding: 0 var(--space-md);
          font-family: var(--family-base);
          font-size: 16px;
          font-weight: 400;
          color: var(--color-text-primary);
          background-color: var(--color-surface);
          border: 1px solid var(--color-border-strong);
          border-radius: var(--radius-input);
          outline: none;
          transition: border-color 0.15s, box-shadow 0.15s;
        }

        .auth-card__input:focus {
          border-color: var(--color-accent-primary);
          box-shadow: var(--elevation-focus);
        }

        .auth-card__input--error {
          border-color: var(--color-error);
        }

        .auth-card__input--error:focus {
          border-color: var(--color-error);
          box-shadow: 0 0 0 3px rgba(220,38,38,0.2);
        }

        .auth-card__input--with-toggle {
          padding-right: 44px;
        }

        .auth-card__toggle {
          position: absolute;
          right: 0;
          top: 0;
          height: 44px;
          width: 44px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: none;
          border: none;
          cursor: pointer;
          color: var(--color-text-muted);
          border-radius: 0 var(--radius-input) var(--radius-input) 0;
          padding: 0;
        }

        .auth-card__toggle:focus-visible {
          outline: 2px solid var(--color-focus-ring);
          outline-offset: -2px;
        }

        .auth-card__toggle:hover {
          color: var(--color-text-secondary);
        }

        .field--error {
          font-size: 12px;
          font-weight: 400;
          line-height: 1.5;
          color: var(--color-error);
          margin-top: var(--space-xs);
          display: block;
        }

        .auth-card__checkbox-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: var(--space-lg);
        }

        .auth-card__checkbox-label {
          display: flex;
          align-items: center;
          gap: var(--space-sm);
          font-size: 14px;
          font-weight: 500;
          color: var(--color-text-secondary);
          cursor: pointer;
          user-select: none;
        }

        .auth-card__checkbox {
          width: 16px;
          height: 16px;
          accent-color: var(--color-accent-primary);
          cursor: pointer;
        }

        .auth-card__forgot-link {
          font-size: 14px;
          font-weight: 500;
          color: var(--color-link);
          text-decoration: none;
        }

        .auth-card__forgot-link:hover {
          text-decoration: underline;
        }

        .auth-card__forgot-link:focus-visible {
          outline: 2px solid var(--color-focus-ring);
          outline-offset: 2px;
          border-radius: var(--radius-sm);
        }

        .auth-card__submit {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: var(--space-sm);
          width: 100%;
          height: 44px;
          padding: 0 var(--space-md);
          font-family: var(--family-base);
          font-size: 16px;
          font-weight: 600;
          color: var(--color-surface);
          background-color: var(--color-accent-primary);
          border: none;
          border-radius: var(--radius-button);
          cursor: pointer;
          transition: background-color 0.15s;
          margin-bottom: var(--space-lg);
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
          outline: none;
          box-shadow: var(--elevation-focus);
        }

        .auth-card__spinner {
          width: 18px;
          height: 18px;
          border: 2px solid rgba(255,255,255,0.4);
          border-top-color: #ffffff;
          border-radius: var(--radius-full);
          animation: spin 0.7s linear infinite;
          flex-shrink: 0;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .auth-card__footer {
          text-align: center;
          font-size: 14px;
          font-weight: 500;
          color: var(--color-text-secondary);
          margin: 0;
        }

        .link {
          color: var(--color-link);
          text-decoration: none;
          font-weight: 500;
        }

        .link:hover {
          text-decoration: underline;
        }

        .link:focus-visible {
          outline: 2px solid var(--color-focus-ring);
          outline-offset: 2px;
          border-radius: var(--radius-sm);
        }
      `}</style>

      <div className="login-page">
        <div className="login-page__branding" aria-hidden="false">
          <p className="login-page__brand-name">auth-starter</p>
        </div>

        <form
          className="auth-card"
          aria-labelledby="login-title"
          noValidate
          onSubmit={handleSubmit}
        >
          <h1 className="auth-card__title" id="login-title">
            Sign in
          </h1>

          <div
            role="status"
            aria-live="polite"
            id={formErrorId}
          >
            {hasFormError && (
              <div className="auth-card__banner auth-card__banner--error">
                {errors.form}
              </div>
            )}
          </div>

          <div className="auth-card__field">
            <label className="auth-card__label" htmlFor={emailId}>
              Email address
            </label>
            <div className="auth-card__input-wrapper">
              <input
                id={emailId}
                type="email"
                className={`auth-card__input${errors.email ? ' auth-card__input--error' : ''}`}
                value={values.email}
                onChange={handleEmailChange}
                autoComplete="email"
                aria-describedby={errors.email ? emailErrorId : undefined}
                aria-invalid={errors.email ? 'true' : 'false'}
                disabled={isSubmitting}
                required
              />
            </div>
            {errors.email && (
              <span id={emailErrorId} className="field--error" role="alert">
                {errors.email}
              </span>
            )}
          </div>

          <div className="auth-card__field">
            <label className="auth-card__label" htmlFor={passwordId}>
              Password
            </label>
            <div className="auth-card__input-wrapper">
              <input
                id={passwordId}
                type={showPassword ? 'text' : 'password'}
                className={`auth-card__input auth-card__input--with-toggle${errors.password ? ' auth-card__input--error' : ''}`}
                value={values.password}
                onChange={handlePasswordChange}
                autoComplete="current-password"
                aria-describedby={errors.password ? passwordErrorId : undefined}
                aria-invalid={errors.password ? 'true' : 'false'}
                disabled={isSubmitting}
                required
              />
              <button
                type="button"
                className="auth-card__toggle"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                onClick={handleTogglePassword}
                tabIndex={0}
              >
                {showPassword ? (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
                    <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
                    <line x1="1" y1="1" x2="23" y2="23" />
                  </svg>
                ) : (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                )}
              </button>
            </div>
            {errors.password && (
              <span id={passwordErrorId} className="field--error" role="alert">
                {errors.password}
              </span>
            )}
          </div>

          <div className="auth-card__checkbox-row">
            <label className="auth-card__checkbox-label">
              <input
                type="checkbox"
                className="auth-card__checkbox"
                checked={values.rememberMe}
                onChange={handleRememberMeChange}
                disabled={isSubmitting}
              />
              Remember me
            </label>
            <Link to="/forgot-password" className="auth-card__forgot-link">
              Forgot password?
            </Link>
          </div>

          <button
            type="submit"
            className="auth-card__submit"
            disabled={isSubmitting}
            aria-busy={isSubmitting}
          >
            {isSubmitting && (
              <span className="auth-card__spinner" aria-hidden="true" />
            )}
            {isSubmitting ? 'Signing in…' : 'Sign in'}
          </button>

          <p className="auth-card__footer">
            Don&apos;t have an account?{' '}
            <Link to="/register" className="link">
              Create account
            </Link>
          </p>
        </form>
      </div>
    </>
  );
}
