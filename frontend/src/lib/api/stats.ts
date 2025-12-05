import { get } from './client';
import type { DashboardStats } from '$lib/types';

export async function getDashboardStats(): Promise<DashboardStats> {
	return get<DashboardStats>('/stats/dashboard');
}
