import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from './AuthContext';

interface RequireGuestProps {
  children: React.ReactNode;
}

export function RequireGuest({ children }: RequireGuestProps): JSX.Element {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <></>;
  }

  if (isAuthenticated) {
    return <Navigate to='/profile' replace />;
  }

  return <>{children}</>;
}
