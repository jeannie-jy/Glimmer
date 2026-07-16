import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

interface User { id: string; login: string; name: string; avatar_url: string; }
interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: () => void;
  logout: () => void;
}

const AuthContext = createContext<AuthState>({
  user: null, token: null, loading: true,
  login: () => {}, logout: () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('glimmer_token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for token in URL (OAuth callback)
    const params = new URLSearchParams(window.location.search);
    const urlToken = params.get('token');
    if (urlToken) {
      localStorage.setItem('glimmer_token', urlToken);
      setToken(urlToken);
      // Clean URL
      window.history.replaceState({}, '', '/');
      return;
    }

    if (token) {
      fetch('/api/auth/me', { headers: { Authorization: `Bearer ${token}` } })
        .then(r => r.ok ? r.json() : null)
        .then(u => u ? setUser(u) : (localStorage.removeItem('glimmer_token'), setToken(null)))
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = useCallback(() => { window.location.href = '/api/auth/login'; }, []);
  const logout = useCallback(() => {
    localStorage.removeItem('glimmer_token');
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
