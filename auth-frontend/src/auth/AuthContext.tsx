import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { login as apiLogin, logout as apiLogout, me as apiMe, refresh as apiRefresh, register as apiRegister } from '../api/auth';
import type { LoginRequest, RegisterRequest, UserResponse } from '../api/types';

interface AuthContextValue {
  readonly user: UserResponse | null;
  readonly isAuthenticated: boolean;
  readonly isLoading: boolean;
  readonly login: (data: LoginRequest) => Promise<void>;
  readonly register: (data: RegisterRequest) => Promise<void>;
  readonly logout: () => Promise<void>;
  readonly refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }): JSX.Element {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refresh = useCallback(async (): Promise<void> => {
    try {
      await apiRefresh();
      const currentUser = await apiMe();
      setUser(currentUser);
    } catch {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    apiMe()
      .then((currentUser) => {
        if (!cancelled) {
          setUser(currentUser);
        }
      })
      .catch(async () => {
        if (cancelled) return;
        try {
          await apiRefresh();
          const currentUser = await apiMe();
          if (!cancelled) {
            setUser(currentUser);
          }
        } catch {
          if (!cancelled) {
            setUser(null);
          }
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (data: LoginRequest): Promise<void> => {
    await apiLogin(data);
    const currentUser = await apiMe();
    setUser(currentUser);
  }, []);

  const register = useCallback(async (data: RegisterRequest): Promise<void> => {
    await apiRegister(data);
    const currentUser = await apiMe();
    setUser(currentUser);
  }, []);

  const logout = useCallback(async (): Promise<void> => {
    try {
      await apiLogout();
    } finally {
      setUser(null);
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: user !== null,
      isLoading,
      login,
      register,
      logout,
      refresh,
    }),
    [user, isLoading, login, register, logout, refresh],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
