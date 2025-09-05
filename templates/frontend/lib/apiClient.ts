import {OAuthAgentClient, SessionResponse} from '@curity/token-handler-js-assistant';
import {ApiRemoteError} from '../utilities/apiRemoteError';
import {SessionExpiredError} from '../utilities/sessionExpiredError';

export interface ApiClientConfig {
    bffBaseUrl: string;
    apiPath?: string;
    oauthUserinfoPath?: string;
    auth?: {
        enabled: boolean;
        oauthAgentPath?: string;
        tokenHandlerVersion?: string;
    };
}

export class ApiClient {

    private readonly config: ApiClientConfig;
    private oauthClient: OAuthAgentClient | null = null;
    private sessionResponse: SessionResponse | null = null;

    public constructor(config: ApiClientConfig) {
        this.config = config;

        if (config.auth?.enabled && config.auth?.oauthAgentPath) {
            this.oauthClient = new OAuthAgentClient({
                oauthAgentBaseUrl: `${config.bffBaseUrl}${config.auth.oauthAgentPath}`
            });
        }
    }

    public async handlePageLoad(currentUrl: string = location.href): Promise<SessionResponse | null> {
        if (!this.oauthClient) {
            return null;
        }

        try {
            this.sessionResponse = await this.oauthClient.onPageLoad(currentUrl);

            const url = new URL(currentUrl);
            if (url.pathname.toLowerCase() === '/callback') {
                history.replaceState({}, document.title, '/');
            }

            return this.sessionResponse;
        } catch (error) {
            throw error;
        }
    }

    public async startLogin(options?: any): Promise<{ authorizationUrl: string }> {
        if (!this.oauthClient) {
            throw new Error('Authentication is not configured');
        }

        return await this.oauthClient.startLogin(options);
    }

    public async logout(): Promise<{ logoutUrl?: string }> {
        if (!this.oauthClient) {
            throw new Error('Authentication is not configured');
        }

        return await this.oauthClient.logout();
    }

    public async refresh(): Promise<void> {
        if (!this.oauthClient) {
            throw new Error('Authentication is not configured');
        }

        await this.oauthClient.refresh();
    }

    public isAuthenticated(): boolean {
        return this.sessionResponse?.isLoggedIn || false;
    }

    public getIdTokenClaims(): any {
        return this.sessionResponse?.idTokenClaims || null;
    }

    public async getWelcomeData(): Promise<any> {
        if (!this.config.apiPath) {
            throw new Error('API path is not configured');
        }
        return await this.fetch('POST', `${this.config.apiPath}/data`);
    }

    public async getOAuthUserInfo(): Promise<any> {
        if (!this.config.oauthUserinfoPath) {
            throw new Error('OAuth userinfo path is not configured');
        }
        return await this.fetch('GET', this.config.oauthUserinfoPath);
    }

    public async fetch(method: string, path: string, options?: RequestInit): Promise<any> {
        if (this.config.auth?.enabled && this.oauthClient) {
            return await this.fetchWithAuth(method, path, options);
        } else {
            return await this.fetchWithoutAuth(method, path, options);
        }
    }

    private async fetchWithAuth(method: string, path: string, options?: RequestInit): Promise<any> {
        try {
            return await this.fetchImpl(method, path, options);
        } catch (e1: any) {
            if (e1.status !== 401 || !this.oauthClient) {
                throw e1;
            }

            try {
                await this.oauthClient.refresh();
            } catch (e2: any) {
                if (e2.status == 401) {
                    throw new SessionExpiredError();
                }
                throw e2;
            }

            try {
                return await this.fetchImpl(method, path, options);
            } catch (e3: any) {
                if (e3.status === 401) {
                    throw new SessionExpiredError();
                }
                throw e3;
            }
        }
    }

    private async fetchWithoutAuth(method: string, path: string, options?: RequestInit): Promise<any> {
        return await this.fetchImpl(method, path, options, false);
    }

    private async fetchImpl(method: string, path: string, options?: RequestInit, includeAuth: boolean = true): Promise<any> {
        const url = `${this.config.bffBaseUrl}${path}`;

        const headers: HeadersInit = {
            'accept': 'application/json',
            ...(options?.headers || {})
        };

        if (includeAuth && this.config.auth?.enabled) {
            headers['token-handler-version'] = this.config.auth.tokenHandlerVersion || '1';
        }

        const init: RequestInit = {
            ...options,
            method: method,
            headers: headers,
            mode: 'cors',
        };

        if (includeAuth && this.config.auth?.enabled) {
            init.credentials = 'include';
        }

        const response = await fetch(url, init);
        if (response.ok) {
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.indexOf('application/json') !== -1) {
                return await response.json();
            }
            return await response.text();
        }

        const contentType = response.headers.get('content-type');
        if (contentType && contentType.indexOf('application/json') !== -1) {
            const remoteError = await this.processErrorResponse(response);
            throw remoteError;
        } else {
            throw new ApiRemoteError(response.status, 'server_error', response.statusText);
        }
    }

    private async processErrorResponse(response: Response): Promise<ApiRemoteError> {
        let code = 'server_error';
        let details = '';
        const errorResponse = await response.json();

        if (errorResponse.code) {
            code = errorResponse.code;
        } else if (errorResponse.error_code) {
            code = errorResponse.error_code;
        }

        if (errorResponse.message) {
            details = errorResponse.message;
        } else if (errorResponse.detailed_error) {
            details = errorResponse.detailed_error;
        }

        return new ApiRemoteError(response.status, code, details);
    }
}
