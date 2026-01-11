import {post} from './client';

/*
 * Call the welcome API endpoint
 */
export async function getWelcomeData(): Promise<any> {
    return await post('/');
}
