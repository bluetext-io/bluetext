import React from 'react';
import type {SessionResponse} from '@curity/token-handler-js-assistant';
import {onPageLoad, getUserInfo} from './client';
import {ErrorRenderer} from './utilities/errorRenderer';
import {MultiTabLogout} from './utilities/multiTabLogout';
import {SessionExpiredError} from './utilities/sessionExpiredError';

export function usePhantomTokenHandlerAuth() {

    const [isPageLoaded, setIsPageLoaded] = React.useState(false);
    const [isLoggedIn, setIsLoggedIn] = React.useState(false);
    const [userInfo, setUserInfo] = React.useState<any>(null);
    const [pageLoadError, setPageLoadError] = React.useState('');
    const [sessionResponse, setSessionResponse] = React.useState<SessionResponse | null>(null);

    const multiTabLogoutRef = React.useRef<MultiTabLogout | null>(null);

    React.useEffect(() => {
        startup();
        return () => cleanup();
    }, []);

    async function startup() {

        // Initialize helpers
        multiTabLogoutRef.current = new MultiTabLogout(() => onExternalLogout());
        window.addEventListener('storage', multiTabLogoutRef.current.listenForLoggedOutEvent);

        try {
            // Handle page load
            const response = await onPageLoad(location.href);
            setSessionResponse(response);
            
            // If this is the callback URL, run post-login logic to remove OAuth details from the URL
            const url = new URL(location.href);
            if (url.pathname.toLowerCase() === '/callback') {
                history.replaceState({}, document.title, '/');
            }

            setIsPageLoaded(true);
            setIsLoggedIn(response.isLoggedIn);

            if (response.isLoggedIn) {
                await fetchUserInfo();
            }

            multiTabLogoutRef.current.initialize();

        } catch (e: any) {
            setPageLoadError(ErrorRenderer.toDisplayFormat(e));
        }
    }

    function cleanup() {
        if (multiTabLogoutRef.current) {
            window.removeEventListener('storage', multiTabLogoutRef.current.listenForLoggedOutEvent);
        }
    }

    function onLoggedOut() {
        setIsLoggedIn(false);
        setUserInfo(null);
        if (multiTabLogoutRef.current) {
            multiTabLogoutRef.current.raiseLoggedOutEvent();
        }
    }

    async function fetchUserInfo() {
        try {
            const data = await getUserInfo();
            setUserInfo(data);
        } catch (e: any) {
            if (e instanceof SessionExpiredError) {
                onLoggedOut();
                return;
            }
            // Report error but do not fail startup
            console.error('Problem getting user info', e);
        }
    }

    function onExternalLogout() {
        onLoggedOut();
    }

    return {
        isPageLoaded,
        isLoggedIn,
        userInfo,
        pageLoadError,
        sessionResponse,
        onLoggedOut
    };
}
