import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../features/auth/context/AuthContext';

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
    --elevation-1: 0 1px 2px rgba(15,23,42,0.06);
    --elevation-2: 0 4px 12px rgba(15,23,42,0.08);
    --elevation-card: 0 12px 32px rgba(15,23,42,0.12);
    --elevation-focus: 0 0 0 3px rgba(129,140,248,0.45);
    --family-base: Inter, 'Segoe UI', system-ui, -apple-system, sans-serif;
    --radius-button: 8px;
    --radius-card: 16px;
    --radius-full: 9999px;
    --radius-input: 8px;
    --radius-lg: 12px;
    --radius-sm: 4px;
    --space-2xl: 48px;
    --space-lg: 24px;
    --space-md: 16px;
    --space-sm: 8px;
    --space-xl: 32px;
    --space-xs: 4px;
  }

  .profile-layout {
    min-height: 100vh;
    background-color: var(--color-bg-app);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: var(--space-lg);
    font-family: var(--family-base);
  }

  .profile-branding {
    margin-bottom: var(--space-lg);
    text-align: center;
  }

  .profile-branding__logo {
    font-size: 30px;
    font-weight: 700;
    line-height: 1.2;
    color: var(--color-accent-primary);
    letter-spacing: -0.5px;
  }

  .profile-card {
    background-color: var(--color-surface);
    border-radius: var(--radius-card);
    box-shadow: var(--elevation-card);
    padding: var(--space-2xl);
    width: 100%;
    max-width: 480px;
  }

  .profile-card__title {
    font-size: 30px;
    font-weight: 700;
    line-height: 1.2;
    color: var(--color-text-primary);
    margin: 0 0 var(--space-xs) 0;
  }

  .profile-card__subtitle {
    font-size: 14px;
    font-weight: 500;
    line-height: 1.5;
    color: var(--color-text-secondary);
    margin: 0 0 var(--space-xl) 0;
  }

  .profile-card__avatar {
    display: flex;
    justify-content: center;
    margin-bottom: var(--space-xl);
  }

  .profile-card__avatar-circle {
    width: 80px;
    height: 80px;
    border-radius: var(--radius-full);
    background-color: var(--color-accent-primary);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 30px;
    font-weight: 700;
    color: var(--color-surface);
    line-height: 1;
  }

  .profile-card__fields {
    display: flex;
    flex-direction: column;
    gap: var(--space-md);
    margin-bottom: var(--space-xl);
  }

  .profile-field {
    display: flex;
    flex-direction: column;
    gap: var(--space-xs);
  }

  .profile-field__label {
    font-size: 14px;
    font-weight: 500;
    line-height: 1.5;
    color: var(--color-text-secondary);
  }

  .profile-field__value {
    font-size: 16px;
    font-weight: 400;
    line-height: 1.5;
    color: var(--color-text-primary);
    background-color: var(--color-muted-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-input);
    padding: var(--space-sm) var(--space-md);
  }

  .profile-field__badge {
    display: inline-flex;
    align-items: center;
    gap: var(--space-xs);
    font-size: 12px;
    font-weight: 400;
    line-height: 1.5;
    padding: var(--space-xs) var(--space-sm);
    border-radius: var(--radius-full);
  }

  .profile-field__badge--active {
    background-color: #dcfce7;
    color: var(--color-success);
  }

  .profile-field__badge--inactive {
    background-color: #fee2e2;
    color: var(--color-error);
  }

  .profile-card__divider {
    border: none;
    border-top: 1px solid var(--color-border);
    margin: 0 0 var(--space-xl) 0;
  }

  .profile-card__actions {
    display: flex;
    flex-direction: column;
    gap: var(--space-sm);
  }

  .profile-card__btn {
    width: 100%;
    padding: var(--space-sm) var(--space-md);
    border-radius: var(--radius-button);
    font-size: 16px;
    font-weight: 400;
    line-height: 1.5;
    cursor: pointer;
    transition: background-color 0.15s ease, box-shadow 0.15s ease;
    border: none;
    font-family: var(--family-base);
  }

  .profile-card__btn:focus-visible {
    outline: none;
    box-shadow: var(--elevation-focus);
  }

  .profile-card__btn--logout {
    background-color: var(--color-accent-primary);
    color: var(--color-surface);
  }

  .profile-card__btn--logout:hover:not(:disabled) {
    background-color: var(--color-accent-primary-hover);
  }

  .profile-card__btn--logout:active:not(:disabled) {
    background-color: var(--color-accent-primary-active);
  }

  .profile-card__btn--logout:disabled {
    background-color: var(--color-accent-disabled);
    cursor: not-allowed;
  }

  .profile-card__btn-spinner {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255,255,255,0.4);
    border-top-color: #fff;
    border-radius: var(--radius-full);
    animation: profile-spin 0.6s linear infinite;
    vertical-align: middle;
    margin-right: var(--space-xs);
  }

  @keyframes profile-spin {
    to { transform: rotate(360deg); }
  }

  .profile-card__error {
    font-size: 14px;
    font-weight: 500;
    line-height: 1.5;
    color: var(--color-error);
    background-color: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: var(--radius-input);
    padding: var(--space-sm) var(--space-md);
    margin-bottom: var(--space-md);
  }

  .profile-loading {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    background-color: var(--color-bg-app);
    font-family: var(--family-base);
    font-size: 16px;
    color: var(--color-text-secondary);
  }
`;

function getInitials(fullName: string): string {
  const parts = fullName.trim().split(/\s+/);
  if (parts.length === 0) return '?';
  if (parts.length === 1) return parts[0].charAt(0).toUpperCase();
  return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase();
}

function formatDate(dateString: string): string {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  } catch {
    return dateString;
  }
}

const ProfilePage: React.FC = () => {
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const navigate = useNavigate();
  const [isLoggingOut, setIsLoggingOut] = React.useState(false);
  const [logoutError, setLogoutError] = React.useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate('/login', { replace: true });
    }
  }, [isLoading, isAuthenticated, navigate]);

  if (isLoading) {
    return (
      <>
        <style>{styles}</style>
        <div className='profile-loading' role='status' aria-live='polite'>
          Loading…
        </div>
      </>
    );
  }

  if (!user) {
    return null;
  }

  const handleLogout = async () => {
    setIsLoggingOut(true);
    setLogoutError(null);
    try {
      await logout();
      navigate('/login', { replace: true });
    } catch {
      setLogoutError('Unable to log out. Please try again.');
      setIsLoggingOut(false);
    }
  };

  const initials = getInitials(user.full_name);

  return (
    <>
      <style>{styles}</style>
      <div className='profile-layout'>
        <div className='profile-branding' aria-hidden='true'>
          <span className='profile-branding__logo'>auth-starter</span>
        </div>

        <main className='profile-card' aria-label='Profile'>
          <h1 className='profile-card__title'>Your Profile</h1>
          <p className='profile-card__subtitle'>Manage your account details.</p>

          <div className='profile-card__avatar'>
            <div
              className='profile-card__avatar-circle'
              aria-label={`Avatar for ${user.full_name}`}
              role='img'
            >
              {initials}
            </div>
          </div>

          <div className='profile-card__fields'>
            <div className='profile-field'>
              <span className='profile-field__label' id='label-full-name'>
                Full Name
              </span>
              <div
                className='profile-field__value'
                aria-labelledby='label-full-name'
              >
                {user.full_name}
              </div>
            </div>

            <div className='profile-field'>
              <span className='profile-field__label' id='label-email'>
                Email Address
              </span>
              <div
                className='profile-field__value'
                aria-labelledby='label-email'
              >
                {user.email}
              </div>
            </div>

            <div className='profile-field'>
              <span className='profile-field__label' id='label-status'>
                Account Status
              </span>
              <div aria-labelledby='label-status'>
                <span
                  className={`profile-field__badge ${
                    user.is_active
                      ? 'profile-field__badge--active'
                      : 'profile-field__badge--inactive'
                  }`}
                >
                  {user.is_active ? '✓ Active' : '✗ Inactive'}
                </span>
              </div>
            </div>

            {user.created_at && (
              <div className='profile-field'>
                <span className='profile-field__label' id='label-member-since'>
                  Member Since
                </span>
                <div
                  className='profile-field__value'
                  aria-labelledby='label-member-since'
                >
                  {formatDate(user.created_at)}
                </div>
              </div>
            )}
          </div>

          <hr className='profile-card__divider' />

          {logoutError && (
            <div
              className='profile-card__error'
              role='alert'
              aria-live='polite'
            >
              {logoutError}
            </div>
          )}

          <div className='profile-card__actions'>
            <button
              type='button'
              className='profile-card__btn profile-card__btn--logout'
              onClick={handleLogout}
              disabled={isLoggingOut}
              aria-busy={isLoggingOut}
            >
              {isLoggingOut && (
                <span
                  className='profile-card__btn-spinner'
                  aria-hidden='true'
                />
              )}
              {isLoggingOut ? 'Signing out…' : 'Sign Out'}
            </button>
          </div>
        </main>
      </div>
    </>
  );
};

export default ProfilePage;
