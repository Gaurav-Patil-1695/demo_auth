// Client-side mirror of validation-rules.md
// Rule order and exact messages match the server-side authoritative spec.
// Password policy: minLength=8, requireUppercase=true, requireLowercase=true,
// requireNumber=true, requireSpecialCharacter=false

export const PASSWORD_POLICY = {
  minLength: 8,
  requireUppercase: true,
  requireLowercase: true,
  requireNumber: true,
  requireSpecialCharacter: false,
} as const;

export interface ValidationResult {
  valid: boolean;
  message: string | null;
}

export interface PasswordStrength {
  score: number; // 0-4 (one point per passing rule)
  hasMinLength: boolean;
  hasUppercase: boolean;
  hasLowercase: boolean;
  hasNumber: boolean;
}

// ---------------------------------------------------------------------------
// Individual field validators — messages copied VERBATIM from validation-rules.md
// ---------------------------------------------------------------------------

export function validateFullName(value: string): ValidationResult {
  if (!value || value.trim().length === 0) {
    return { valid: false, message: 'Full name is required.' };
  }
  if (value.trim().length > 100) {
    return { valid: false, message: 'Full name must not exceed 100 characters.' };
  }
  return { valid: true, message: null };
}

export function validateEmail(value: string): ValidationResult {
  if (!value || value.trim().length === 0) {
    return { valid: false, message: 'Email is required.' };
  }
  // RFC-5322 simplified pattern
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailPattern.test(value.trim())) {
    return { valid: false, message: 'Enter a valid email address.' };
  }
  return { valid: true, message: null };
}

export function validatePassword(value: string): ValidationResult {
  if (!value || value.length === 0) {
    return { valid: false, message: 'Password is required.' };
  }
  if (value.length < PASSWORD_POLICY.minLength) {
    return {
      valid: false,
      message: `Password must be at least ${PASSWORD_POLICY.minLength} characters.`,
    };
  }
  if (PASSWORD_POLICY.requireUppercase && !/[A-Z]/.test(value)) {
    return {
      valid: false,
      message: 'Password must contain at least one uppercase letter.',
    };
  }
  if (PASSWORD_POLICY.requireLowercase && !/[a-z]/.test(value)) {
    return {
      valid: false,
      message: 'Password must contain at least one lowercase letter.',
    };
  }
  if (PASSWORD_POLICY.requireNumber && !/[0-9]/.test(value)) {
    return {
      valid: false,
      message: 'Password must contain at least one number.',
    };
  }
  return { valid: true, message: null };
}

export function validateConfirmPassword(
  password: string,
  confirmPassword: string,
): ValidationResult {
  if (!confirmPassword || confirmPassword.length === 0) {
    return { valid: false, message: 'Please confirm your password.' };
  }
  if (password !== confirmPassword) {
    return { valid: false, message: 'Passwords do not match.' };
  }
  return { valid: true, message: null };
}

export function validateTerms(accepted: boolean): ValidationResult {
  if (!accepted) {
    return {
      valid: false,
      message: 'You must accept the Terms of Service to continue.',
    };
  }
  return { valid: true, message: null };
}

export function validateResetToken(value: string): ValidationResult {
  if (!value || value.trim().length === 0) {
    return { valid: false, message: 'Reset token is required.' };
  }
  return { valid: true, message: null };
}

// ---------------------------------------------------------------------------
// Password strength helper (used by PasswordStrengthMeter)
// Checks exactly the four active rules; special character is NOT required.
// ---------------------------------------------------------------------------

export function getPasswordStrength(value: string): PasswordStrength {
  const hasMinLength = value.length >= PASSWORD_POLICY.minLength;
  const hasUppercase = /[A-Z]/.test(value);
  const hasLowercase = /[a-z]/.test(value);
  const hasNumber = /[0-9]/.test(value);

  const score = [
    hasMinLength,
    hasUppercase,
    hasLowercase,
    hasNumber,
  ].filter(Boolean).length;

  return { score, hasMinLength, hasUppercase, hasLowercase, hasNumber };
}

// ---------------------------------------------------------------------------
// Form-level validators — validate all fields at once, return a map of
// field name -> error message (null means no error)
// ---------------------------------------------------------------------------

export interface LoginFormErrors {
  email: string | null;
  password: string | null;
}

export function validateLoginForm(
  email: string,
  password: string,
): LoginFormErrors {
  return {
    email: validateEmail(email).message,
    password: !password || password.length === 0 ? 'Password is required.' : null,
  };
}

export interface RegisterFormErrors {
  fullName: string | null;
  email: string | null;
  password: string | null;
  confirmPassword: string | null;
  terms: string | null;
}

export function validateRegisterForm(
  fullName: string,
  email: string,
  password: string,
  confirmPassword: string,
  termsAccepted: boolean,
): RegisterFormErrors {
  return {
    fullName: validateFullName(fullName).message,
    email: validateEmail(email).message,
    password: validatePassword(password).message,
    confirmPassword: validateConfirmPassword(password, confirmPassword).message,
    terms: validateTerms(termsAccepted).message,
  };
}

export interface ForgotPasswordFormErrors {
  email: string | null;
}

export function validateForgotPasswordForm(
  email: string,
): ForgotPasswordFormErrors {
  return {
    email: validateEmail(email).message,
  };
}

export interface ResetPasswordFormErrors {
  password: string | null;
  confirmPassword: string | null;
}

export function validateResetPasswordForm(
  password: string,
  confirmPassword: string,
): ResetPasswordFormErrors {
  return {
    password: validatePassword(password).message,
    confirmPassword: validateConfirmPassword(password, confirmPassword).message,
  };
}

// ---------------------------------------------------------------------------
// Utility: check whether a form-errors object has any error
// ---------------------------------------------------------------------------

export function hasErrors(
  errors: Record<string, string | null>,
): boolean {
  return Object.values(errors).some((msg) => msg !== null);
}
