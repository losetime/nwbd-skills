<template>
    <div class="mx-auto max-w-3xl pt-12">
        <div class="flex items-end justify-between">
            <div>
                <p class="text-[11px] font-medium tracking-[0.18em] text-ink-faint uppercase">Accounts</p>
                <h1 class="mt-3 font-display text-[28px] leading-tight text-ink">账号</h1>
                <p class="mt-2 text-[12.5px] text-ink-soft">首次钉钉扫码登录会自动建号；角色随钉钉管理员列表同步。</p>
            </div>
        </div>

        <div class="mt-6 overflow-hidden rounded-2xl border border-line bg-white">
            <table class="w-full">
                <thead>
                    <tr class="border-b border-line">
                        <th class="px-5 py-3 text-left text-[10.5px] font-medium tracking-[0.08em] text-ink-faint uppercase">账号</th>
                        <th class="px-3 py-3 text-left text-[10.5px] font-medium tracking-[0.08em] text-ink-faint uppercase">角色</th>
                        <th class="px-3 py-3 text-left text-[10.5px] font-medium tracking-[0.08em] text-ink-faint uppercase">状态</th>
                        <th class="px-5 py-3 text-right text-[10.5px] font-medium tracking-[0.08em] text-ink-faint uppercase"></th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="user in users" :key="user.id" class="border-b border-line/70 last:border-0">
                        <td class="px-5 py-3">
                            <div class="text-[13px] text-ink">{{ user.display_name || user.username }}</div>
                            <div class="mt-0.5 font-mono text-[10.5px] text-ink-faint">{{ user.username }}</div>
                        </td>
                        <td class="px-3 py-3">
                            <div class="relative inline-block">
                                <select class="appearance-none border border-line bg-white py-1 pl-2 pr-7 text-[11.5px] text-ink-soft" :value="user.role" @change="changeRole(user, ($event.target as HTMLSelectElement).value)">
                                    <option value="member">成员</option>
                                    <option value="admin">管理员</option>
                                </select>
                                <svg class="pointer-events-none absolute right-2 top-1/2 h-3 w-3 -translate-y-1/2 text-ink-faint" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="m6 9 6 6 6-6" />
                                </svg>
                            </div>
                        </td>
                        <td class="px-3 py-3">
                            <span class="chip" :class="user.enabled ? 'text-ink-soft' : 'text-ink-faint'">{{ user.enabled ? "启用" : "停用" }}</span>
                        </td>
                        <td class="px-5 py-3 text-right">
                            <button class="text-[11.5px] text-ink-faint transition hover:text-ink" @click="toggle(user)">
                                {{ user.enabled ? "停用" : "启用" }}
                            </button>
                        </td>
                    </tr>
                </tbody>
            </table>
            <div v-if="!users.length" class="px-5 py-14 text-center text-[12.5px] text-ink-faint">暂无账号</div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";

import { listUsers, updateUser, type User } from "@/@api/auth";

defineOptions({ name: "UsersPage" });

const users = ref<User[]>([]);

/**
 * 加载账号列表。
 * 调用时机：页面挂载与任何修改成功后。
 */
async function load() {
    const result = await listUsers();
    users.value = result.items;
}

/**
 * 修改账号角色。
 * 调用时机：角色下拉框变更时。
 */
async function changeRole(user: User, role: string) {
    await updateUser(user.id, { role });
    await load();
}

/**
 * 启用或停用账号。
 * 调用时机：点击行尾启停按钮时。
 */
async function toggle(user: User) {
    await updateUser(user.id, { enabled: !user.enabled });
    await load();
}

onMounted(load);
</script>
