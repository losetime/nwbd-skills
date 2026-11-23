/** 账号接口。调用时机：登录页、顶部用户信息与用户管理页。 */

import { request } from "./http";

export interface User {
    id: string;
    username: string;
    display_name: string;
    role: "member" | "admin";
    enabled: boolean;
    created_at: string;
}

export interface AuthConfig {
    enabled: boolean;
    clientId: string;
    redirectUri: string;
}

export interface LoginResult {
    access_token: string;
    token_type: string;
    user: User;
}

/**
 * 读取扫码登录配置。
 * 调用时机：登录页初始化二维码前。
 */
export function fetchAuthConfig(): Promise<AuthConfig> {
    return request<AuthConfig>("/api/auth/config");
}

/**
 * 用扫码授权码换取登录令牌。
 * 调用时机：钉钉登录组件回调拿到 authCode 后。
 */
export function exchangeDingTalk(authCode: string): Promise<LoginResult> {
    return request<LoginResult>("/api/auth/dingtalk/exchange", {
        method: "POST",
        body: JSON.stringify({ auth_code: authCode }),
    });
}

/**
 * 读取当前登录用户。
 * 调用时机：刷新页面后恢复登录态时。
 */
export function fetchMe(): Promise<User> {
    return request<User>("/api/auth/me");
}

/**
 * 分页读取账号列表。
 * 调用时机：用户管理页加载时。
 */
export function listUsers(page = 1, size = 50): Promise<{ items: User[]; total: number }> {
    return request(`/api/users?page=${page}&size=${size}`);
}

/**
 * 修改账号角色或启停状态。
 * 调用时机：用户管理页切换角色、启停时。
 */
export function updateUser(id: string, payload: { role?: string; enabled?: boolean }): Promise<User> {
    return request<User>(`/api/users/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
}
