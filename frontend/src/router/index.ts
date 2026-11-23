/** 路由表与访问守卫。调用时机：应用启动时注册，每次导航时校验登录态。 */

import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

import AppLayout from "@/layouts/AppLayout.vue";
import { useAuthStore } from "@/store/auth";

const routes: RouteRecordRaw[] = [
    { path: "/login", name: "login", component: () => import("@/views/login/Login.vue") },
    {
        path: "/",
        component: AppLayout,
        children: [
            { path: "", name: "skills", component: () => import("@/views/skills/SkillWall.vue") },
            {
                path: "upload",
                name: "upload",
                component: () => import("@/views/skills/SkillUpload.vue"),
                meta: { requiresAuth: true },
            },
            { path: "skills/:name", name: "skill-detail", component: () => import("@/views/skills/SkillDetail.vue") },
            {
                path: "settings/users",
                name: "users",
                component: () => import("@/views/settings/Users.vue"),
                meta: { requiresAuth: true, admin: true },
            },
            {
                path: "settings/audit",
                name: "audit",
                component: () => import("@/views/settings/Audit.vue"),
                meta: { requiresAuth: true, admin: true },
            },
        ],
    },
    { path: "/:pathMatch(.*)*", redirect: "/" },
];

export const router = createRouter({
    history: createWebHistory(),
    routes,
});

router.beforeEach(async (to) => {
    const auth = useAuthStore();
    // 有令牌但还没取到用户信息时补一次，用于刷新后恢复登录态
    if (auth.isLoggedIn && !auth.user) {
        await auth.restore();
    }
    if (to.meta.requiresAuth && !auth.isLoggedIn) {
        return { name: "login", query: { redirect: to.fullPath } };
    }
    if (to.meta.admin && !auth.isAdmin) {
        return { name: "skills" };
    }
    if (to.name === "login" && auth.isLoggedIn) {
        return { name: "skills" };
    }
    return true;
});
