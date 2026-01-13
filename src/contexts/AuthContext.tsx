/**
 * Authentication Context
 * 
 * Provides authentication state and methods throughout the React app.
 * Connects to Flask session-based auth via /auth/api/* endpoints.
 */

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { api } from '../api/client';
import { ENDPOINTS } from '../api/endpoints';

// Types
interface User {
    username: string;
}

interface AuthState {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
}

interface AuthContextType extends AuthState {
    login: (username: string, password: string) => Promise<{ success: boolean; error?: string }>;
    logout: () => Promise<void>;
    checkAuth: () => Promise<void>;
}

// API Response types
interface LoginResponse {
    status: 'success' | 'error';
    user?: User;
    message?: string;
}

interface StatusResponse {
    authenticated: boolean;
    user: User | null;
}

// Create context with undefined default
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Provider component
interface AuthProviderProps {
    children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
    const [state, setState] = useState<AuthState>({
        user: null,
        isAuthenticated: false,
        isLoading: true, // Start with loading to check existing session
    });

    // Check authentication status
    const checkAuth = useCallback(async () => {
        setState(prev => ({ ...prev, isLoading: true }));

        const result = await api.get<StatusResponse>(ENDPOINTS.AUTH_API_STATUS);

        if (result.success && result.data.authenticated) {
            setState({
                user: result.data.user,
                isAuthenticated: true,
                isLoading: false,
            });
        } else {
            setState({
                user: null,
                isAuthenticated: false,
                isLoading: false,
            });
        }
    }, []);

    // Login function
    const login = useCallback(async (username: string, password: string): Promise<{ success: boolean; error?: string }> => {
        setState(prev => ({ ...prev, isLoading: true }));

        const result = await api.post<LoginResponse>(ENDPOINTS.AUTH_API_LOGIN, { username, password });

        if (result.success && result.data.status === 'success' && result.data.user) {
            setState({
                user: result.data.user,
                isAuthenticated: true,
                isLoading: false,
            });
            return { success: true };
        } else {
            setState(prev => ({ ...prev, isLoading: false }));
            const errorMessage = result.success
                ? result.data.message || 'Login failed'
                : result.error.message;
            return { success: false, error: errorMessage };
        }
    }, []);

    // Logout function
    const logout = useCallback(async () => {
        setState(prev => ({ ...prev, isLoading: true }));

        await api.post(ENDPOINTS.AUTH_API_LOGOUT);

        setState({
            user: null,
            isAuthenticated: false,
            isLoading: false,
        });
    }, []);

    // Check auth on mount
    useEffect(() => {
        checkAuth();
    }, [checkAuth]);

    const value: AuthContextType = {
        ...state,
        login,
        logout,
        checkAuth,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

// Custom hook to use auth context
export const useAuth = (): AuthContextType => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

export default AuthContext;
