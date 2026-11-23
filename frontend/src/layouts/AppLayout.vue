<template>
    <div class="min-h-full bg-paper">
        <header class="sticky top-0 z-30 bg-paper/80 backdrop-blur-xl">
            <div class="mx-auto flex h-[68px] max-w-6xl items-center gap-4 px-6">
                <router-link to="/" class="flex shrink-0 items-center gap-2.5">
                    <span class="flex h-8 w-8 items-center justify-center rounded-[10px] bg-ink font-display text-[15px] text-white">N</span>
                    <span class="hidden font-display text-[15px] tracking-tight text-ink sm:block">诺维技能库</span>
                </router-link>

                <nav class="ml-auto flex shrink-0 items-center gap-0.5 rounded-full border border-line/90 bg-white/70 p-1">
                    <router-link v-for="item in nav" :key="item.to" :to="item.to" class="nav-pill">
                        {{ item.label }}
                    </router-link>
                </nav>

                <div class="relative shrink-0">
                    <router-link
                        v-if="!auth.isLoggedIn"
                        to="/login"
                        class="flex items-center gap-1.5 border border-line bg-white/70 px-3 py-1.5 text-[12px] text-ink-soft transition hover:border-ink/25 hover:text-ink"
                    >
                        登录
                    </router-link>
                    <template v-else>
                        <button class="flex items-center gap-2 rounded-full border border-line bg-white/70 py-1 pl-1 pr-2 transition hover:border-ink/25 sm:pr-3" @click="menuOpen = !menuOpen">
                            <span class="flex h-7 w-7 items-center justify-center rounded-full bg-ink text-[11px] font-medium text-white">
                                {{ initials }}
                            </span>
                            <span class="hidden text-[12px] text-ink-soft sm:block">{{ displayName }}</span>
                        </button>

                        <div v-if="menuOpen" class="absolute right-0 top-11 w-44 overflow-hidden rounded-xl border border-line bg-white py-1 shadow-[0_12px_32px_rgba(18,19,22,0.10)]">
                            <div class="px-3 py-2 text-[11px] text-ink-faint">{{ auth.isAdmin ? "管理员" : "成员" }}</div>
                            <router-link v-if="auth.isAdmin" to="/settings/users" class="menu-item" @click="menuOpen = false">账号</router-link>
                            <router-link v-if="auth.isAdmin" to="/settings/audit" class="menu-item" @click="menuOpen = false">审计</router-link>
                            <button class="menu-item w-full text-left text-accent" @click="logout">退出登录</button>
                        </div>
                    </template>
                </div>
            </div>
        </header>

        <main class="mx-auto max-w-6xl px-6 pb-24">
            <router-view />
        </main>

        <div v-if="menuOpen" class="fixed inset-0 z-20" @click="menuOpen = false"></div>
    </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useRouter } from "vue-router";

import { useAuthStore } from "@/store/auth";

defineOptions({ name: "AppLayout" });

const auth = useAuthStore();
const router = useRouter();
const menuOpen = ref(false);

const nav = computed(() => [
    { to: "/", label: "技能" },
    ...(auth.isLoggedIn ? [{ to: "/upload", label: "上传" }] : []),
]);

const displayName = computed(() => auth.user?.display_name || auth.user?.username || "");

const initials = computed(() => (displayName.value || "?").slice(0, 1).toUpperCase());

/**
 * 退出登录并回到登录页。
 * 调用时机：用户菜单点击退出时。
 */
function logout() {
    menuOpen.value = false;
    auth.logout();
    router.push({ name: "login" });
}
</script>

<style scoped>
@reference "../style.css";

.nav-pill {
    @apply whitespace-nowrap rounded-full px-3.5 py-1.5 text-[13px] text-ink-soft transition-colors duration-150;
}

.nav-pill:hover {
    @apply text-ink;
}

.nav-pill.router-link-exact-active {
    @apply bg-ink text-white;
}

.menu-item {
    @apply block px-3 py-2 text-[13px] text-ink-soft transition-colors hover:bg-paper-deep hover:text-ink;
}
</style>
