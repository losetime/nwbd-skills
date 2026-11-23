<template>
    <div class="mx-auto max-w-4xl pt-12">
        <div class="flex items-end justify-between">
            <div>
                <p class="text-[11px] font-medium tracking-[0.18em] text-ink-faint uppercase">Audit</p>
                <h1 class="mt-3 font-display text-[28px] leading-tight text-ink">审计</h1>
                <p class="mt-2 text-[12.5px] text-ink-soft">共 {{ total }} 条记录，按时间倒序。</p>
            </div>
            <div class="relative w-36">
                <select v-model="action" class="field appearance-none pr-9">
                    <option value="">全部动作</option>
                    <option value="upload">上传</option>
                    <option value="publish">发布</option>
                    <option value="deprecate">废弃</option>
                    <option value="restore">恢复</option>
                    <option value="version_delete">删除版本</option>
                    <option value="transfer">转移归属</option>
                    <option value="delete">删除技能</option>
                    <option value="user_create">新建账号</option>
                    <option value="user_update">修改账号</option>
                    <option value="login_failed">登录失败</option>
                    <option value="register">注册</option>
                </select>
                <svg class="pointer-events-none absolute right-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-ink-faint" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                    <path d="m6 9 6 6 6-6" />
                </svg>
            </div>
        </div>

        <div class="mt-6 overflow-hidden rounded-2xl border border-line bg-white">
            <table class="w-full table-fixed">
                <colgroup>
                    <col class="w-[150px]" />
                    <col class="w-[92px]" />
                    <col class="w-[200px]" />
                    <col class="w-[180px]" />
                    <col />
                </colgroup>
                <thead>
                    <tr class="border-b border-line">
                        <th class="px-5 py-3 text-left text-[10.5px] font-medium tracking-[0.08em] text-ink-faint uppercase">时间</th>
                        <th class="px-3 py-3 text-left text-[10.5px] font-medium tracking-[0.08em] text-ink-faint uppercase">动作</th>
                        <th class="px-3 py-3 text-left text-[10.5px] font-medium tracking-[0.08em] text-ink-faint uppercase">操作人</th>
                        <th class="px-3 py-3 text-left text-[10.5px] font-medium tracking-[0.08em] text-ink-faint uppercase">技能</th>
                        <th class="px-5 py-3 text-left text-[10.5px] font-medium tracking-[0.08em] text-ink-faint uppercase">明细</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="row in items" :key="row.id" class="border-b border-line/70 last:border-0">
                        <td class="whitespace-nowrap px-5 py-2.5 font-mono text-[11px] text-ink-faint">{{ formatTime(row.at) }}</td>
                        <td class="px-3 py-2.5">
                            <span class="chip" :class="tone(row.action)">{{ label(row.action) }}</span>
                        </td>
                        <td class="truncate px-3 py-2.5 text-[12.5px] text-ink" :title="row.actor">{{ row.actor || "—" }}</td>
                        <td class="px-3 py-2.5 text-[12.5px] text-ink">
                            <span class="block truncate">
                                {{ row.skill || "—" }}
                                <span v-if="row.version" class="ml-1 font-mono text-[11px] text-ink-faint">v{{ row.version }}</span>
                            </span>
                        </td>
                        <td class="truncate px-5 py-2.5 font-mono text-[10.5px] text-ink-faint" :title="JSON.stringify(row.detail)">
                            {{ JSON.stringify(row.detail) }}
                        </td>
                    </tr>
                </tbody>
            </table>
            <div v-if="!items.length" class="px-5 py-14 text-center text-[12.5px] text-ink-faint">暂无记录</div>
        </div>

        <div v-if="total > size" class="mt-5 flex items-center justify-between text-[12px] text-ink-faint">
            <span>第 {{ page }} / {{ Math.ceil(total / size) }} 页</span>
            <div class="flex gap-2">
                <button class="btn-quiet px-3 py-1.5" :disabled="page <= 1" @click="go(page - 1)">上一页</button>
                <button class="btn-quiet px-3 py-1.5" :disabled="page >= Math.ceil(total / size)" @click="go(page + 1)">下一页</button>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from "vue";

import { listAudit, type AuditItem } from "@/@api/skills";

defineOptions({ name: "AuditPage" });

const items = ref<AuditItem[]>([]);
const total = ref(0);
const page = ref(1);
const size = ref(30);
const action = ref("");

/**
 * 请求审计记录。
 * 调用时机：页面挂载、筛选变化与翻页时。
 */
async function load() {
    const result = await listAudit({ action: action.value, page: page.value, size: size.value });
    items.value = result.items;
    total.value = result.total;
}

/**
 * 筛选变化后回到第一页。
 * 调用时机：动作下拉框变化时。
 */
watch(action, () => {
    page.value = 1;
    void load();
});

/**
 * 翻页。
 * 调用时机：点击分页按钮时。
 */
function go(target: number) {
    page.value = target;
    void load();
}

onMounted(load);

const actionText: Record<string, string> = {
    upload: "上传",
    publish: "发布",
    deprecate: "废弃",
    // 历史记录的兼容映射：这两个动作已下线，但旧数据仍在
    rollback: "设为当前",
    archive: "归档",
    restore: "恢复",
    version_delete: "删除版本",
    transfer: "转移归属",
    delete: "删除技能",
    login_failed: "登录失败",
    register: "注册",
    user_create: "新建账号",
    user_update: "修改账号",
    password_change: "修改密码",
};

/**
 * 动作中文名。
 * 调用时机：渲染动作列时。
 */
function label(value: string): string {
    return actionText[value] ?? value;
}

/**
 * 动作配色。
 * 调用时机：渲染动作列时。
 */
function tone(value: string): string {
    if (value === "login_failed" || value === "delete" || value === "version_delete") return "border-accent/30 bg-accent-soft/60 text-accent";
    if (value === "deprecate") return "border-amber-200 bg-amber-50 text-amber-700";
    if (value === "restore") return "border-emerald-200 bg-emerald-50 text-emerald-700";
    return "";
}

/**
 * 格式化时间。
 * 调用时机：渲染时间列时。
 */
function formatTime(value: string): string {
    return new Date(value).toLocaleString("zh-CN", { hour12: false });
}
</script>
