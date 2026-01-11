import {OAuthAgentRemoteError} from '@curity/token-handler-js-assistant';
import {ApiRemoteError} from './apiRemoteError';

/*
 * The SPA renders OAuth or API errors in its preferred manner
 */
export class ErrorRenderer {

    public static toDisplayFormat(error: any): string {

        let component = '';
        let status = 0;
        let code = '';
        let details = '';

        if (error instanceof OAuthAgentRemoteError) {

            component = 'OAuth Agent';
            status = error.status;
            code = error.code;
            details = error.details || '';
        } 
        else if (error instanceof ApiRemoteError) {

            component = 'API'
            status = error.status;
            code = error.code;
            details = error.details || '';
        } 
        else {

            if (error.status) {
                status = error.status;
            }
            details = error.message || '';
        }

        const parts = [];
        if (component) {
            parts.push(`Problem encountered calling ${component}`);
        } else {
            parts.push('Problem encountered');
        }

        if (status) {
            parts.push(`status: ${status}`);
        }

        if (code) {
            parts.push(`code: ${code}`);
        }

        if (details) {
            parts.push(`details: ${details}`);
        }

        return parts.join(', ');
    }
}
