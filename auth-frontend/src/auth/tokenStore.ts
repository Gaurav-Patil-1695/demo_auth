/**
 * tokenStore
 *
 * Access token is kept in module-level memory only — never written to
 * localStorage or sessionStorage so it cannot be read by XSS scripts.
 *
 * The refresh token is stored exclusively in an httpOnly cookie that is
 * set by the backend; this module never reads or writes that cookie.
 */

let accessToken: string | null = null;

/**
 * Store the access token in memory.
 */
export function setAccessToken(token: string): void {
  accessToken = token;
}

/**
 * Retrieve the current in-memory access token, or null if none is stored.
 */
export function getAccessToken(): string | null {
  return accessToken;
}

/**
 * Clear the in-memory access token (e.g. on logout).
 */
export function clearAccessToken(): void {
  accessToken = null;
}
