import { useState, useCallback, ChangeEvent, FocusEvent, FormEvent } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type FieldValues = Record<string, string | boolean>;

export type FieldErrors = Record<string, string>;

export type TouchedFields = Record<string, boolean>;

export interface UseAuthFormOptions<T extends FieldValues> {
  initialValues: T;
  validate: (values: T) => FieldErrors;
  onSubmit: (values: T) => Promise<void>;
}

export interface UseAuthFormReturn<T extends FieldValues> {
  values: T;
  errors: FieldErrors;
  touched: TouchedFields;
  isSubmitting: boolean;
  submitError: string;
  submitSuccess: boolean;
  handleChange: (e: ChangeEvent<HTMLInputElement>) => void;
  handleBlur: (e: FocusEvent<HTMLInputElement>) => void;
  handleSubmit: (e: FormEvent<HTMLFormElement>) => void;
  setSubmitError: (message: string) => void;
  setSubmitSuccess: (value: boolean) => void;
  resetForm: () => void;
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useAuthForm<T extends FieldValues>({
  initialValues,
  validate,
  onSubmit,
}: UseAuthFormOptions<T>): UseAuthFormReturn<T> {
  const [values, setValues] = useState<T>(initialValues);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [touched, setTouched] = useState<TouchedFields>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const [submitSuccess, setSubmitSuccess] = useState(false);

  // -------------------------------------------------------------------------
  // Handlers
  // -------------------------------------------------------------------------

  const handleChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const { name, type, checked, value } = e.target;
      const fieldValue: string | boolean = type === 'checkbox' ? checked : value;

      setValues((prev) => ({ ...prev, [name]: fieldValue }));

      // Re-validate touched field on every change so the error clears as soon
      // as the user satisfies the rule.
      setTouched((prevTouched) => {
        if (prevTouched[name]) {
          const nextValues = { ...values, [name]: fieldValue } as T;
          const nextErrors = validate(nextValues);
          setErrors(nextErrors);
        }
        return prevTouched;
      });
    },
    [values, validate],
  );

  const handleBlur = useCallback(
    (e: FocusEvent<HTMLInputElement>) => {
      const { name } = e.target;

      setTouched((prev) => ({ ...prev, [name]: true }));

      // Run validation on the full current values so cross-field rules work.
      const nextErrors = validate(values);
      setErrors(nextErrors);
    },
    [values, validate],
  );

  const handleSubmit = useCallback(
    async (e: FormEvent<HTMLFormElement>) => {
      e.preventDefault();

      // Mark every field as touched so all errors surface at once.
      const allTouched: TouchedFields = Object.keys(values).reduce(
        (acc, key) => ({ ...acc, [key]: true }),
        {},
      );
      setTouched(allTouched);

      const validationErrors = validate(values);
      setErrors(validationErrors);

      if (Object.keys(validationErrors).length > 0) {
        return;
      }

      setIsSubmitting(true);
      setSubmitError('');
      setSubmitSuccess(false);

      try {
        await onSubmit(values);
        setSubmitSuccess(true);
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : 'An unexpected error occurred.';
        setSubmitError(message);
      } finally {
        setIsSubmitting(false);
      }
    },
    [values, validate, onSubmit],
  );

  const resetForm = useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
    setIsSubmitting(false);
    setSubmitError('');
    setSubmitSuccess(false);
  }, [initialValues]);

  return {
    values,
    errors,
    touched,
    isSubmitting,
    submitError,
    submitSuccess,
    handleChange,
    handleBlur,
    handleSubmit,
    setSubmitError,
    setSubmitSuccess,
    resetForm,
  };
}
