const API_BASE_URL = '/api/v1';

interface RequestOptions extends RequestInit {
	params?: Record<string, string | number | boolean | string[] | undefined>;
}

class ApiError extends Error {
	constructor(
		public status: number,
		message: string
	) {
		super(message);
		this.name = 'ApiError';
	}
}

function buildUrl(path: string, params?: Record<string, string | number | boolean | string[] | undefined>): string {
	const url = new URL(`${API_BASE_URL}${path}`, window.location.origin);
	
	if (params) {
		Object.entries(params).forEach(([key, value]) => {
			if (value !== undefined && value !== null) {
				if (Array.isArray(value)) {
					value.forEach((v) => url.searchParams.append(key, String(v)));
				} else {
					url.searchParams.append(key, String(value));
				}
			}
		});
	}
	
	return url.toString();
}

async function handleResponse<T>(response: Response): Promise<T> {
	if (!response.ok) {
		const errorText = await response.text();
		throw new ApiError(response.status, errorText || response.statusText);
	}
	return response.json();
}

export async function get<T>(path: string, options: RequestOptions = {}): Promise<T> {
	const { params, ...fetchOptions } = options;
	const url = buildUrl(path, params);
	
	const response = await fetch(url, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			...fetchOptions.headers
		},
		...fetchOptions
	});
	
	return handleResponse<T>(response);
}

export async function post<T, D = unknown>(path: string, data?: D, options: RequestOptions = {}): Promise<T> {
	const { params, ...fetchOptions } = options;
	const url = buildUrl(path, params);
	
	const response = await fetch(url, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			...fetchOptions.headers
		},
		body: data ? JSON.stringify(data) : undefined,
		...fetchOptions
	});
	
	return handleResponse<T>(response);
}

export { ApiError };
