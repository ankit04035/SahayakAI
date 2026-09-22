import React, { createContext, useContext, useState, ReactNode } from 'react';

interface UserContextType {
  userId: number;
  setUserId: (id: number) => void;
  userName: string;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export const UserProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  // Default to developer user ID 1 in pre-auth mode
  const [userId, setUserId] = useState<number>(1);
  const userName = `Student Developer (ID #${userId})`;

  return (
    <UserContext.Provider value={{ userId, setUserId, userName }}>
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
