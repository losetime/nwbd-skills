/** 接口请求封装。调用时机：所有业务模块通过 @api 下的方法间接调用。 */

export interface FieldIssue {
    field: string;
    message: string;
}

export class ApiError extends Error {
    code: string;
    details: FieldIssue[];

    constructor(code: string, message: string, details: FieldIssue[] = []) {
        super(message);
        this.code = code;
        this.details = details;
    }
}

const TOKEN_KEY = "nwbd-skills-token";

export function getToken(): string {
    return localStorage.getItem(TOKEN_KEY) ?? "";
}

export function setToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
    localStorage.removeItem(TOKEN_KEY);
}

/**
 * 发起请求并解包统一响应结构。
 * 调用时机：各业务接口方法内部调用，业务代码不直接使用。
 */
export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers = new Headers(init.headers);
    if (!(init.body instanceof FormData)) {
        headers.set("Content-Type", "application/json");
    }
    const token = getToken();
    if (token) {
        headers.set("Authorization", `Bearer ${token}`);
    }

    const response = await fetch(path, { ...init, headers });
    const text = await response.text();
    let payload: { code?: string | number; message?: string; details?: FieldIssue[]; data?: unknown } = {};
    if (text) {
        try {
            payload = JSON.parse(text);
        } catch {
            payload = {};
        }
    }

    // 只有带着令牌的 401 才算登录失效；登录接口自己的 401 是账号密码错误
    if (response.status === 401 && token) {
        clearToken();
        if (location.pathname !== "/login") {
            location.href = "/login";
        }
        throw new ApiError("UNAUTHORIZED", "登录已失效，请重新登录");
    }

    if (!response.ok || payload.code !== 0) {
        throw new ApiError(String(payload.code ?? "HTTP_ERROR"), payload.message ?? "请求失败", payload.details ?? []);
    }
    return payload.data as T;
}
