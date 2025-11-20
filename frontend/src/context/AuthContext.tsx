import React, { createContext, useContext, useEffect, useState } from "react";
import api from "../api/client";
import type { UserCreate, UserLogin, UserRead } from "../api/types";

type AuthContextType = {
  user: UserRead | null;
  token: string | null;
  login: (payload: UserLogin) => Promise<void>;
  register: (payload: UserCreate) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = "tripplanner_token";
const USER_KEY = "tripplanner_user";

export const getToken = (): string | null => {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserRead | null>(null);
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const storedToken = localStorage.getItem(TOKEN_KEY);
    const storedUser = localStorage.getItem(USER_KEY);
    if (storedToken) setToken(storedToken);
    if (storedUser) setUser(JSON.parse(storedUser));
  }, []);

  const login = async (payload: UserLogin) => {
    const { data } = await api.post("/auth/login", payload);
    setToken(data.access_token);
    setUser(data.user);
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(data.user));
  };

  const register = async (payload: UserCreate) => {
    await api.post("/auth/register", payload);
    await login({ email: payload.email, password: payload.password });
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
};
