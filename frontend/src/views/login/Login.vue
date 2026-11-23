<template>
    <div class="flex min-h-screen bg-paper">
        <!-- 左侧陈述 -->
        <section class="relative hidden w-[52%] flex-col justify-between overflow-hidden bg-ink p-12 lg:flex">
            <div class="grain"></div>
            <div class="flex items-center gap-2.5">
                <span class="flex h-8 w-8 items-center justify-center rounded-[10px] bg-white font-display text-[15px] text-ink">N</span>
                <span class="font-display text-[15px] text-white/90">诺维技能库</span>
            </div>

            <div class="relative z-10 max-w-md">
                <p class="font-display text-[40px] leading-[1.25] tracking-tight text-white">
                    技能写一次，<br />
                    团队就能<FlipWords :words="['复用', '检索', '交付']" class="text-[#e9b98a]" />，<br />
                    随时取用。
                </p>
                <p class="mt-6 text-[13px] leading-7 text-white/45">
                    集中管理 SKILL.md 指令包：上传、校验、版本、发布与分发，一处完成。
                </p>
            </div>

            <div class="relative z-10 flex items-center gap-6 text-[11px] text-white/30">
                <span>nwbd-skills</span>
                <span>·</span>
                <span>内部使用</span>
            </div>
        </section>

        <!-- 右侧二维码 -->
        <section class="flex flex-1 items-center justify-center px-6 py-16">
            <div class="w-full max-w-[360px]">
                <p class="text-[11px] font-medium tracking-[0.18em] text-ink-faint uppercase">Sign in</p>
                <h1 class="mt-3 font-display text-[28px] leading-tight text-ink">登录</h1>
                <p class="mt-2 text-[12.5px] text-ink-soft">使用钉钉扫码登录</p>

                <div class="mt-7">
                    <div id="dingtalk_qr" class="flex min-h-[320px] w-[300px] items-center justify-center border border-line bg-white">
                        <span v-if="status === 'loading'" class="text-[12px] text-ink-faint">二维码加载中…</span>
                    </div>
                </div>

                <p v-if="message" class="mt-4 max-w-[300px] text-[11.5px] leading-5" :class="status === 'error' ? 'text-accent' : 'text-ink-faint'">
                    {{ message }}
                </p>

                <button v-if="status === 'error'" class="btn-solid mt-4 w-[300px] py-2.5" @click="start">
                    重新加载二维码
                </button>

                <p class="mt-6 text-[12px] text-ink-faint">
                    <router-link to="/" class="underline-offset-2 transition hover:text-ink hover:underline">暂不登录，先逛逛 →</router-link>
                </p>
            </div>
        </section>
    </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { fetchAuthConfig } from "@/@api/auth";
import FlipWords from "@/components/inspira/FlipWords.vue";
import { useAuthStore } from "@/store/auth";

defineOptions({ name: "LoginPage" });

declare global {
    interface Window {
        DTFrameLogin?: (
            frameParams: Record<string, unknown>,
            loginParams: Record<string, unknown>,
            success: (result: { authCode?: string }) => void,
            fail: (error: string) => void,
        ) => void;
    }
}

const auth = useAuthStore();
const route = useRoute();

const status = ref<"loading" | "qr" | "error">("loading");
const message = ref("");

/**
 * 动态加载钉钉登录 SDK。
 * 调用时机：拿到登录配置后、渲染二维码前。
 */
function loadSdk(): Promise<void> {
    return new Promise((resolve, reject) => {
        if (window.DTFrameLogin) {
            resolve();
            return;
        }
        const script = document.createElement("script");
        script.src = "https://g.alicdn.com/dingding/h5-dingtalk-login/0.21.0/ddlogin.js";
        script.onload = () => resolve();
        script.onerror = () => reject(new Error("钉钉登录组件加载失败，请检查网络"));
        document.head.appendChild(script);
    });
}

/**
 * 扫码成功后把授权码交给后端换成登录令牌。
 * 调用时机：SDK 回调拿到 authCode 时。
 */
async function exchange(authCode: string) {
    status.value = "loading";
    message.value = "正在登录…";
    try {
        await auth.loginWithDingtalk(authCode);
        const raw = typeof route.query.redirect === "string" ? route.query.redirect : "";
        // 不用 router.replace：钉钉扫码完成后可能同时触发整页回跳，SPA 导航会被打断
        const target = raw && !raw.startsWith("/login") ? raw : "/";
        window.location.replace(target);
    } catch (err) {
        status.value = "error";
        message.value = err instanceof Error ? err.message : "登录失败";
    }
}

/**
 * 初始化二维码。
 * 调用时机：页面挂载与点击「重新加载二维码」时。
 */
async function start() {
    status.value = "loading";
    message.value = "";
    try {
        const config = await fetchAuthConfig();
        if (!config.enabled) {
            status.value = "error";
            message.value = "管理员还没有配置钉钉登录，请联系系统管理员。";
            return;
        }
        await loadSdk();
        status.value = "qr";
        await nextTick();
        window.DTFrameLogin?.(
            { id: "dingtalk_qr", width: 300, height: 320 },
            {
                redirect_uri: encodeURIComponent(config.redirectUri),
                client_id: config.clientId,
                scope: "openid",
                response_type: "code",
                prompt: "consent",
                state: "skills",
            },
            (result) => {
                if (result?.authCode) void exchange(result.authCode);
                else {
                    status.value = "error";
                    message.value = "未拿到授权码，请重新扫码";
                }
            },
            (error) => {
                status.value = "error";
                message.value = `钉钉登录组件报错：${error}`;
            },
        );
    } catch (err) {
        status.value = "error";
        message.value = err instanceof Error ? err.message : "登录页初始化失败";
    }
}

onMounted(async () => {
    // 钉钉有时会把授权码直接回跳到 /login?code=xxx，这里兜住
    const code = typeof route.query.code === "string" ? route.query.code : "";
    if (code) {
        await exchange(code);
        return;
    }
    // 已经登录（比如扫码后页面被刷新）直接进站
    if (auth.isLoggedIn) {
        window.location.replace("/");
        return;
    }
    await start();
});
</script>

<style scoped>
.grain {
    position: absolute;
    inset: 0;
    background-image: radial-gradient(circle at 18% 22%, rgba(201, 80, 44, 0.28), transparent 42%),
        radial-gradient(circle at 78% 72%, rgba(255, 255, 255, 0.08), transparent 46%);
}
</style>
