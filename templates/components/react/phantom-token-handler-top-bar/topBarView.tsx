import React from 'react';
import { useAuth } from '../../integrations/api/modules/phantom-token-handler-secured-api-client/AuthContext';
import { startLogin, logout } from '../../integrations/api/client';
import { ErrorRenderer } from '../../integrations/api/modules/phantom-token-handler-secured-api-client/utilities/errorRenderer';
import './topBar.css';

export function TopBarView() {
    const { isLoggedIn, userInfo, onLoggedOut } = useAuth();
    const [initials, setInitials] = React.useState('');
    const [showDropdown, setShowDropdown] = React.useState(false);
    const dropdownRef = React.useRef<HTMLDivElement>(null);

    React.useEffect(() => {
        if (userInfo) {
            if (userInfo.name.givenName && userInfo.name.familyName) {
                const first = userInfo.name.givenName.charAt(0).toUpperCase();
                const last = userInfo.name.familyName.charAt(0).toUpperCase();
                setInitials(`${first}${last}`);
            } else if (userInfo.sub) {
                 setInitials(userInfo.sub.substring(0, 2).toUpperCase());
            } else {
                 setInitials('??');
            }
        }
    }, [userInfo]);

    // Close dropdown when clicking outside
    React.useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setShowDropdown(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, []);

    async function handleLogin() {
        try {
            const response = await startLogin();
            location.href = response.authorizationUrl;
        } catch (e: any) {
             alert(ErrorRenderer.toDisplayFormat(e));
        }
    }

    async function handleLogout() {
        try {
            const logoutResponse = await logout();
            onLoggedOut();
             if (logoutResponse.logoutUrl) {
                location.href = logoutResponse.logoutUrl;
            } else {
                location.href = location.origin
            }
        } catch (e: any) {
            if (e.status === 401) {
                onLoggedOut();
                return;
            }
             alert(ErrorRenderer.toDisplayFormat(e));
        }
    }

    return (
        <div className="top-bar">
            <div className="top-bar-left">
                Logo
            </div>
            <div className="top-bar-right">
                {!isLoggedIn && (
                    <button 
                        className="btn btn-primary btn-sm"
                        onClick={handleLogin}
                    >
                        Login
                    </button>
                )}

                {isLoggedIn && (
                    <div ref={dropdownRef}>
                        <div 
                            className="profile-circle"
                            onClick={() => setShowDropdown(!showDropdown)}
                        >
                            {initials}
                        </div>
                        <div className={`dropdown-menu-custom ${showDropdown ? 'show' : ''}`}>
                             <button className="dropdown-item-custom" onClick={handleLogout}>
                                Logout
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
