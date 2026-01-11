/*
 * Indicates refresh token expiry
 */
export class SessionExpiredError extends Error {

    constructor() {
        super('Login required');
    }
}
