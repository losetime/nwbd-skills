/** 登录状态。调用时机：路由守卫、登录页与侧边栏共享当前用户。 */

import { defineStore } from "pinia";

import { exchangeDingTalk, fetchMe, type User } from "@/@api/auth";
import { clearToken, getToken, setToken } from "@/@api/http";

interface AuthState {
    token: string;
    user: User | null;
    loading: boolean;
}

export const useAuthStore = defineStore("auth", {
    state: (): AuthState => ({
        token: getToken(),
        user: null,
        loading: false,
    }),
    getters: {
        isLoggedIn: (state) => Boolean(state.token),
        isAdmin: (state) => state.user?.role === "admin",
    },
    actions: {
        /**
         * 钉钉扫码登录并保存令牌。
         * 调用时机：登录页拿到 authCode 后。
         */
        async loginWithDingtalk(authCode: string) {
            const result = await exchangeDingTalk(authCode);
            this.token = result.access_token;
            this.user = result.user;
            setToken(result.access_token);
        },

        /**
         * 恢复登录态。
         * 调用时机：路由守卫首次进入受保护页面时调用一次。
         */
        async restore() {
            if (!getToken()) return;
            this.loading = true;
            try {
                this.user = await fetchMe();
            } catch {
                this.logout();
            } finally {
                this.loading = false;
            }
        },

        /**
         * 清除本地登录状态。
         * 调用时机：点击退出登录或令牌失效时。
         */
        logout() {
            this.token = "";
            this.user = null;
            clearToken();
        },
    },
});
