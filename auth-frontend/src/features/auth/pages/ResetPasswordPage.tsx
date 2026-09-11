import React, { useState } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { resetPassword } from '../../../api/auth';

const styles = `
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
    --elevation-card: 0 12px 32px rgba(15,23,42,0.12);
    --elevation-focus: 0 0 0 3px rgba(129,140,248,0.45);
    --family-base: Inter, 'Segoe UI', system-ui, -apple-system, sans-serif;
    --radius-button: 8px;
    --radius-card: 16px;
    --radius-input: 8px;
    --space-2xl: 48px;
    --space-lg: 24px;
    --space-md: 16px;
    --space-sm: 8px;
    --space-xl: 32px;
    --space-xs: 4px;
  }

  .reset-password-app {
    min-height: 100vh;
    background-color: var(--color-bg-app);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    font-family: var(--family-base);
    padding: var(--space-lg);
  }

  .reset-password-app__branding {
    margin-bottom: var(--space-lg);
    text-align: center;
  }

  .reset-password-app__logo {
    font-size: 24px;
    font-weight: 700;
    color: var(--color-accent-primary);
    text-decoration: none;
    letter-spacing: -0.5px;
  }

  .auth-card {
    background: var(--color-surface);
    border-radius: var(--radius-card);
    box-shadow: var(--elevation-card);
    padding: var(--space-2xl);
    width: 100%;
    max-width: 420px;
  }

  .auth-card__title {
    font-size: 30px;
    font-weight: 700;
    line-height: 1.2;
    color: var(--color-text-primary);
    margin: 0 0 var(--space-sm) 0;
  }

  .auth-card__subtitle {
    font-size: 14px;
    font-weight: 400;
    line-height: 1.5;
    color: var(--color-text-secondary);
    margin: 0 0 var(--space-xl) 0;
  }

  .auth-card__field {
    margin-bottom: var(--space-md);
  }

  .auth-card__label {
    display: block;
    font-size: 14px;
    font-weight: 500;
    color: var(--color-text-primary);
    margin-bottom: var(--space-xs);
  }

  .auth-card__input-wrapper {
    position: relative;
    display: flex;
    align-items: center;
  }

  .auth-card__input {
    width: 100%;
    padding: 10px var(--space-md);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-input);
    font-size: 16px;
    font-family: var(--family-base);
    color: var(--color-text-primary);
    background: var(--color-surface);
    outline: none;
    transition: border-color 0.15s, box-shadow 0.15s;
    box-sizing: border-box;
  }

  .auth-card__input:focus {
    border-color: var(--color-accent-primary);
    box-shadow: var(--elevation-focus);
  }

  .auth-card__input--error {
    border-color: var(--color-error);
  }

  .auth-card__input--with-toggle {
    padding-right: 44px;
  }

  .auth-card__toggle-btn {
    position: absolute;
    right: var(--space-sm);
    background: none;
    border: none;
    cursor: pointer;
    color: var(--color-text-muted);
    padding: var(--space-xs);
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: var(--radius-sm);
    transition: color 0.15s;
  }

  .auth-card__toggle-btn:hover {
    color: var(--color-text-secondary);
  }

  .field--error {
    font-size: 12px;
    color: var(--color-error);
    margin-top: var(--space-xs);
    line-height: 1.5;
  }

  .auth-card__strength {
    margin-top: var(--space-xs);
  }

  .auth-card__strength-bars {
    display: flex;
    gap: var(--space-xs);
    margin-bottom: var(--space-xs);
  }

  .auth-card__strength-bar {
    height: 4px;
    flex: 1;
    border-radius: var(--radius-full, 9999px);
    background: var(--color-border);
    transition: background 0.2s;
  }

  .auth-card__strength-bar--weak {
    background: var(--color-error);
  }

  .auth-card__strength-bar--fair {
    background: var(--color-warning);
  }

  .auth-card__strength-bar--strong {
    background: var(--color-success);
  }

  .auth-card__strength-label {
    font-size: 12px;
    color: var(--color-text-muted);
    line-height: 1.5;
  }

  .auth-card__submit {
    width: 100%;
    padding: 11px var(--space-lg);
    background: var(--color-accent-primary);
    color: var(--color-surface);
    border: none;
    border-radius: var(--radius-button);
    font-size: 16px;
    font-weight: 600;
    font-family: var(--family-base);
    cursor: pointer;
    transition: background 0.15s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-sm);
    margin-top: var(--space-lg);
  }

  .auth-card__submit:hover:not(:disabled) {
    background: var(--color-accent-primary-hover);
  }

  .auth-card__submit:active:not(:disabled) {
    background: var(--color-accent-primary-active);
  }

  .auth-card__submit:disabled {
    background: var(--color-accent-disabled);
    cursor: not-allowed;
  }

  .auth-card__spinner {
    width: 18px;
    height: 18px;
    border: 2px solid rgba(255,255,255,0.4);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .auth-card__banner {
    border-radius: var(--radius-input);
    padding: var(--space-sm) var(--space-md);
    font-size: 14px;
    line-height: 1.5;
    margin-bottom: var(--space-md);
  }

  .auth-card__banner--error {
    background: #fef2f2;
    color: var(--color-error);
    border: 1px solid #fecaca;
  }

  .auth-card__banner--success {
    background: #f0fdf4;
    color: var(--color-success);
    border: 1px solid #bbf7d0;
  }

  .auth-card__footer {
    margin-top: var(--space-lg);
    text-align: center;
    font-size: 14px;
    color: var(--color-text-secondary);
  }

  .auth-card__link {
    color: var(--color-link);
    text-decoration: none;
    font-weight: 500;
  }

  .auth-card__link:hover {
    text-decoration: underline;
  }
`;

function getStrengthScore(password: string): number {
  let score = 0;
  if (password.length >= 8) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[a-z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  return score;
}

function getStrengthLabel(score: number): string {
  if (score <= 1) return 'Weak';
  if (score <= 2) return 'Fair';
  if (score <= 3) return 'Good';
  return 'Strong';
}

function getBarClass(barIndex: number, score: number): string {
  if (score === 0) return 'auth-card__strength-bar';
  if (barIndex >= score) return 'auth-card__strength-bar';
  if (score <= 1) return 'auth-card__strength-bar auth-card__strength-bar--weak';
  if (score <= 2) return 'auth-card__strength-bar auth-card__strength-bar--fair';
  return 'auth-card__strength-bar auth-card__strength-bar--strong';
}

interface FormErrors {
  password?: string;
  confirmPassword?: string;
}

function validateForm(password: string, confirmPassword: string): FormErrors {
  const errors: FormErrors = {};

  if (!password) {
    errors.password = 'Password is required.';
  } else if (password.length < 8) {
    errors.password = 'Password must be at least 8 characters.';
  } else if (!/[A-Z]/.test(password)) {
    errors.password = 'Password must contain at least one uppercase letter.';
  } else if (!/[a-z]/.test(password)) {
    errors.password = 'Password must contain at least one lowercase letter.';
  } else if (!/[0-9]/.test(password)) {
    errors.password = 'Password must contain at least one number.';
  }

  if (!confirmPassword) {
    errors.confirmPassword = 'Please confirm your password.';
  } else if (password && confirmPassword !== password) {
    errors.confirmPassword = 'Passwords do not match.';
  }

  return errors;
}

const ResetPasswordPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token') ?? '';

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<FormErrors>({});
  const [bannerError, setBannerError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const strengthScore = getStrengthScore(password);

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPassword(e.target.value);
    if (fieldErrors.password) {
      setFieldErrors((prev) => ({ ...prev, password: undefined }));
    }
  };

  const handleConfirmPasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setConfirmPassword(e.target.value);
    if (fieldErrors.confirmPassword) {
      setFieldErrors((prev) => ({ ...prev, confirmPassword: undefined }));
    }
  };

  const handleTogglePassword = () => {
    setShowPassword((prev) => !prev);
  };

  const handleToggleConfirmPassword = () => {
    setShowConfirmPassword((prev) => !prev);
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setBannerError('');
    setSuccessMessage('');

    const errors = validateForm(password, confirmPassword);
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }

    if (!token) {
      setBannerError('Reset token is missing or invalid. Please request a new password reset link.');
      return;
    }

    setIsSubmitting(true);
    try {
      await resetPassword({ token, password, confirmPassword });
      setSuccessMessage('Your password has been reset successfully. You can now log in.');
      setTimeout(() => {
        navigate('/login');
      }, 2500);
    } catch (err: unknown) {
      if (
        err &&
        typeof err === 'object' &&
        'response' in err &&
        err.response &&
        typeof err.response === 'object' &&
        'data' in err.response
      ) {
        const data = (err as { response: { data: { error?: { message?: string } } } }).response.data;
        setBannerError(data?.error?.message ?? 'Failed to reset password. Please try again.');
      } else {
        setBannerError('Failed to reset password. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <style>{styles}</style>
      <div className='reset-password-app'>
        <div className='reset-password-app__branding'>
          <a href='/' className='reset-password-app__logo'>
            AuthStarter
          </a>
        </div>
        <div className='auth-card'>
          <h1 className='auth-card__title'>Set new password</h1>
          <p className='auth-card__subtitle'>
            Choose a strong password for your account.
          </p>

          <div aria-live='polite'>
            {bannerError && (
              <div className='auth-card__banner auth-card__banner--error' role='alert'>
                {bannerError}
              </div>
            )}
            {successMessage && (
              <div className='auth-card__banner auth-card__banner--success' role='status'>
                {successMessage}
              </div>
            )}
          </div>

          <form onSubmit={handleSubmit} noValidate>
            <div className='auth-card__field'>
              <label htmlFor='password' className='auth-card__label'>
                New Password
              </label>
              <div className='auth-card__input-wrapper'>
                <input
                  id='password'
                  type={showPassword ? 'text' : 'password'}
                  className={
                    'auth-card__input auth-card__input--with-toggle' +
                    (fieldErrors.password ? ' auth-card__input--error' : '')
                  }
                  value={password}
                  onChange={handlePasswordChange}
                  autoComplete='new-password'
                  aria-describedby={fieldErrors.password ? 'password-error' : 'password-strength'}
                  aria-invalid={!!fieldErrors.password}
                  disabled={isSubmitting || !!successMessage}
                />
                <button
                  type='button'
                  className='auth-card__toggle-btn'
                  onClick={handleTogglePassword}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  tabIndex={0}
                >
                  {showPassword ? (
                    <svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' strokeWidth='2' strokeLinecap='round' strokeLinejoin='round'>
                      <path d='M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24' />
                      <line x1='1' y1='1' x2='23' y2='23' />
                    </svg>
                  ) : (
                    <svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' strokeWidth='2' strokeLinecap='round' strokeLinejoin='round'>
                      <path d='M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z' />
                      <circle cx='12' cy='12' r='3' />
                    </svg>
                  )}
                </button>
              </div>
              {fieldErrors.password && (
                <div id='password-error' className='field--error' role='alert'>
                  {fieldErrors.password}
                </div>
              )}
              {password && !fieldErrors.password && (
                <div className='auth-card__strength' id='password-strength'>
                  <div className='auth-card__strength-bars' aria-hidden='true'>
                    {[0, 1, 2, 3].map((i) => (
                      <div key={i} className={getBarClass(i, strengthScore)} />
                    ))}
                  </div>
                  <div className='auth-card__strength-label'>
                    Password strength: {getStrengthLabel(strengthScore)}
                  </div>
                </div>
              )}
            </div>

            <div className='auth-card__field'>
              <label htmlFor='confirmPassword' className='auth-card__label'>
                Confirm New Password
              </label>
              <div className='auth-card__input-wrapper'>
                <input
                  id='confirmPassword'
                  type={showConfirmPassword ? 'text' : 'password'}
                  className={
                    'auth-card__input auth-card__input--with-toggle' +
                    (fieldErrors.confirmPassword ? ' auth-card__input--error' : '')
                  }
                  value={confirmPassword}
                  onChange={handleConfirmPasswordChange}
                  autoComplete='new-password'
                  aria-describedby={fieldErrors.confirmPassword ? 'confirm-password-error' : undefined}
                  aria-invalid={!!fieldErrors.confirmPassword}
                  disabled={isSubmitting || !!successMessage}
                />
                <button
                  type='button'
                  className='auth-card__toggle-btn'
                  onClick={handleToggleConfirmPassword}
                  aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                  tabIndex={0}
                >
                  {showConfirmPassword ? (
                    <svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' strokeWidth='2' strokeLinecap='round' strokeLinejoin='round'>
                      <path d='M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24' />
                      <line x1='1' y1='1' x2='23' y2='23' />
                    </svg>
                  ) : (
                    <svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' strokeWidth='2' strokeLinecap='round' strokeLinejoin='round'>
                      <path d='M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z' />
                      <circle cx='12' cy='12' r='3' />
                    </svg>
                  )}
                </button>
              </div>
              {fieldErrors.confirmPassword && (
                <div id='confirm-password-error' className='field--error' role='alert'>
                  {fieldErrors.confirmPassword}
                </div>
              )}
            </div>

            <button
              type='submit'
              className='auth-card__submit'
              disabled={isSubmitting || !!successMessage}
              aria-busy={isSubmitting}
            >
              {isSubmitting && <span className='auth-card__spinner' aria-hidden='true' />}
              {isSubmitting ? 'Resetting…' : 'Reset Password'}
            </button>
          </form>

          <div className='auth-card__footer'>
            <Link to='/login' className='auth-card__link'>
              Back to Sign In
            </Link>
          </div>
        </div>
      </div>
    </>
  );
};

export default ResetPasswordPage;
