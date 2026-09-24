/** Operations that load the role-scoped portal state. */
import { request } from '../core/client';
import type { State, UiFeaturesAccess } from './state.types';

export const getState = () => request<State>('state');
export const getUiFeaturesAccess = () => request<UiFeaturesAccess>('admin/ui-features');
