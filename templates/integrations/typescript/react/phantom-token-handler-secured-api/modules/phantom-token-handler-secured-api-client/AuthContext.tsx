import React from 'react';
import { usePhantomTokenHandlerAuth } from './usePhantomTokenHandlerAuth';

type AuthContextType = ReturnType<typeof useBffAuth>;

const AuthContext = React.createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const auth = usePhantomTokenHandlerAuth();
    
    return (
        <AuthContext.Provider value={auth}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = React.useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
