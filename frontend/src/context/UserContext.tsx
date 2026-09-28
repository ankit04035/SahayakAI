import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { AuthUser, getCurrentUser, loginAccount, logoutAccount, registerAccount } from '../api/auth';
import { ApiError } from '../api/client';

interface UserContextType {
  userId: number;
  user: AuthUser | null;
  loading: boolean;
  register: (payload: { name: string; email: string; password: string }) => Promise<void>;
  login: (payload: { email: string; password: string }) => Promise<void>;
  logout: () => Promise<void>;
  userName: string;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export const UserProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    getCurrentUser()
      .then((currentUser) => {
        if (active) setUser(currentUser);
      })
      .catch(() => {
        if (active) setUser(null);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const register = async (payload: { name: string; email: string; password: string }) => {
    setUser(await registerAccount(payload));
  };

  const login = async (payload: { email: string; password: string }) => {
    setUser(await loginAccount(payload));
  };

  const logout = async () => {
    try {
      await logoutAccount();
    } catch (error) {
      if (!(error instanceof ApiError) || error.status !== 401) throw error;
    }
    setUser(null);
  };

  const userId = user?.id ?? 0;
  const userName = user?.name ?? '';

  return (
    <UserContext.Provider value={{ userId, user, loading, register, login, logout, userName }}>
      {children}
    </UserContext.Provider>
  );
};

export const useUser = (): UserContextType => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
};
