import { get } from './client';
import type { DashboardStats } from '$lib/types';

export async function getDashboardStats(days: number = 7): Promise<DashboardStats> {
	return get<DashboardStats>('/stats/dashboard', { params: { days } });
}
