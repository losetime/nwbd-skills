<template>
    <section class="relative pt-10">
        <div class="pointer-events-none absolute inset-x-0 -top-20 h-[360px] overflow-hidden">
            <InteractiveGridPattern />
            <div class="absolute inset-0 bg-gradient-to-b from-transparent via-paper/40 to-paper" />
        </div>
        <div class="relative">
            <p class="text-[11px] font-medium tracking-[0.18em] text-ink-faint uppercase">Skill Library</p>
            <div class="mt-3 flex flex-col gap-4 sm:flex-row sm:flex-wrap sm:items-end sm:justify-between">
                <TextGenerateEffect text="技能库" tag="h1" class="font-display text-[34px] leading-tight tracking-tight text-ink" :stagger="70" />
                <div class="flex flex-wrap items-center gap-3 text-[12.5px] text-ink-faint">
                    <span><NumberTicker :value="stats.skill_count" class="font-medium text-ink" /> 个技能</span>
                    <span class="text-line">·</span>
                    <span><NumberTicker :value="stats.version_count" class="font-medium text-ink" /> 个版本</span>
                    <span class="text-line">·</span>
                    <span><NumberTicker :value="stats.published_count" class="font-medium text-ink" /> 已发布</span>
                </div>
            </div>
        </div>

        <div class="relative mt-7 flex items-center gap-3">
            <div class="halo-wrap relative flex-1">
                <svg class="pointer-events-none absolute left-4 top-1/2 z-10 h-4 w-4 -translate-y-1/2 text-ink-faint" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                    <circle cx="11" cy="11" r="7" />
                    <path d="m20 20-3.5-3.5" />
                </svg>
                <input v-model="keyword" class="field halo-input pl-11" placeholder="搜索技能名称或描述" />
            </div>

        </div>
    </section>

    <section class="mt-6">
        <div v-if="loading" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div v-for="i in 3" :key="i" class="h-46 animate-pulse rounded-2xl border border-line bg-white/60"></div>
        </div>

        <div v-else-if="items.length" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <CardSpotlight v-for="(item, index) in items" :key="item.name" class="card-in" :style="{ animationDelay: `${index * 40}ms` }">
                <router-link
                    :to="`/skills/${item.name}`"
                    class="group relative flex h-full flex-col overflow-hidden border border-line bg-white p-5 transition-all duration-200 hover:-translate-y-0.5 hover:border-ink/15 hover:shadow-[0_12px_34px_rgba(18,19,22,0.08)]"
                    @mouseenter="enter"
                    @mousemove="glide"
                >
                    <span class="glare" />
                    <BorderBeam class="z-20 opacity-0 transition-opacity duration-300 group-hover:opacity-100" :duration="4.5" />

                    <div class="relative z-10 flex items-start justify-between">
                        <span class="flex h-10 w-10 items-center justify-center font-display text-[15px] text-white/95" :style="glyph(item.name)">
                            {{ item.name.slice(0, 1).toUpperCase() }}
                        </span>
                        <span v-if="item.current_version" class="chip">v{{ item.current_version }}</span>
                        <span v-else class="chip text-ink-faint">未发布</span>
                    </div>

                    <h3 class="relative z-10 mt-4 font-display text-[17px] tracking-tight text-ink">{{ item.name }}</h3>
                    <p class="relative z-10 mt-1.5 line-clamp-2 text-[13px] leading-6 text-ink-soft">
                        <template v-if="keyword">
                            <span v-for="(part, partIndex) in highlight(item.summary || '暂无描述')" :key="partIndex" :class="part.hit ? 'rounded bg-accent/12 px-0.5 text-ink' : ''">{{ part.text }}</span>
                        </template>
                        <template v-else>{{ item.summary || "暂无描述" }}</template>
                    </p>

                    <div class="relative z-10 mt-auto flex items-center gap-2.5 pt-5 text-[11px] text-ink-faint">
                        <span>{{ item.file_count }} 个文件</span>
                        <span class="text-line">·</span>
                        <span>{{ formatSize(item.size_bytes) }}</span>
                        <span class="ml-auto">{{ formatDate(item.updated_at) }}</span>
                    </div>
                </router-link>
            </CardSpotlight>

            <router-link
                v-if="!keyword && auth.isLoggedIn"
                to="/upload"
                class="card-in shimmer-tile flex min-h-[196px] flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-ink/15 text-ink-faint transition-all duration-200 hover:-translate-y-0.5 hover:border-ink/30 hover:text-ink"
                :style="{ animationDelay: `${items.length * 40}ms` }"
            >
                <span class="flex h-9 w-9 items-center justify-center rounded-full border border-line bg-white/70">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                        <path d="M12 5v14M5 12h14" />
                    </svg>
                </span>
                <span class="text-[12.5px]">上传新技能</span>
            </router-link>
        </div>

        <div v-else class="shell-card flex flex-col items-center justify-center px-6 py-24 text-center">
            <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-paper-deep text-ink-faint">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
                    <path d="M21 8 12 3 3 8v8l9 5 9-5Z" />
                    <path d="M3 8l9 5 9-5" />
                </svg>
            </div>
            <p class="mt-4 font-display text-[16px] text-ink">{{ keyword ? "没有匹配的技能" : "技能库还是空的" }}</p>
            <p class="mt-1 text-[13px] text-ink-faint">{{ keyword ? "换个关键词试试" : "上传一个 zip 包就能开始" }}</p>
            <router-link v-if="!keyword && auth.isLoggedIn" to="/upload" class="btn-solid mt-5">上传第一个技能</router-link>
        </div>

        <div v-if="total > size" class="mt-6 flex items-center justify-between text-[12px] text-ink-faint">
            <span>第 {{ page }} / {{ Math.ceil(total / size) }} 页</span>
            <div class="flex gap-2">
                <button class="btn-quiet px-3 py-1.5" :disabled="page <= 1" @click="go(page - 1)">上一页</button>
                <button class="btn-quiet px-3 py-1.5" :disabled="page >= Math.ceil(total / size)" @click="go(page + 1)">下一页</button>
            </div>
        </div>
    </section>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from "vue";

import { getStats, listSkills, type SkillSummary, type Stats } from "@/@api/skills";
import { useAuthStore } from "@/store/auth";
import BorderBeam from "@/components/inspira/BorderBeam.vue";
import CardSpotlight from "@/components/inspira/CardSpotlight.vue";
import InteractiveGridPattern from "@/components/inspira/InteractiveGridPattern.vue";
import NumberTicker from "@/components/inspira/NumberTicker.vue";
import TextGenerateEffect from "@/components/inspira/TextGenerateEffect.vue";

defineOptions({ name: "SkillWallPage" });

const auth = useAuthStore();

const items = ref<SkillSummary[]>([]);
const total = ref(0);
const page = ref(1);
const size = ref(24);
const keyword = ref("");
const loading = ref(true);
const stats = ref<Stats>({ skill_count: 0, version_count: 0, published_count: 0, recent: [] });

let timer: ReturnType<typeof setTimeout> | undefined;

/**
 * 请求技能列表。
 * 调用时机：页面挂载、搜索防抖后、筛选变化与翻页时。
 */
async function load() {
    loading.value = true;
    try {
        const result = await listSkills({ q: keyword.value, page: page.value, size: size.value });
        items.value = result.items;
        total.value = result.total;
    } finally {
        loading.value = false;
    }
}

/**
 * 读取顶部统计。
 * 调用时机：页面挂载时。
 */
async function loadStats() {
    stats.value = await getStats();
}

watch(keyword, () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
        page.value = 1;
        void load();
    }, 300);
});


/**
 * 翻页。
 * 调用时机：点击分页按钮时。
 */
function go(target: number) {
    page.value = target;
    void load();
}

onMounted(() => {
    void load();
    void loadStats();
});

/**
 * 依据技能名生成稳定渐变色。
 * 调用时机：渲染卡片图标时。
 */
function glyph(name: string) {
    let hash = 0;
    for (let i = 0; i < name.length; i += 1) hash = (hash * 31 + name.charCodeAt(i)) % 360;
    const from = `hsl(${hash} 42% 46%)`;
    const to = `hsl(${(hash + 38) % 360} 46% 34%)`;
    return { background: `linear-gradient(140deg, ${from}, ${to})` };
}

/**
 * 记录鼠标进入方向，决定高光扫入的角度（改编自 Direction Aware Hover 与 Glare Card）。
 * 调用时机：指针进入卡片时。
 */
function enter(event: MouseEvent) {
    const element = event.currentTarget as HTMLElement;
    const rect = element.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const distances = [x, rect.width - x, y, rect.height - y];
    const nearest = distances.indexOf(Math.min(...distances));
    const angle = nearest === 0 ? 90 : nearest === 1 ? 270 : nearest === 2 ? 180 : 0;
    element.style.setProperty("--gx", `${angle}deg`);
}

/**
 * 让高光跟随指针在卡片内移动。
 * 调用时机：指针在卡片内移动时。
 */
function glide(event: MouseEvent) {
    const element = event.currentTarget as HTMLElement;
    const rect = element.getBoundingClientRect();
    element.style.setProperty("--px", `${((event.clientX - rect.left) / rect.width) * 100}%`);
    element.style.setProperty("--py", `${((event.clientY - rect.top) / rect.height) * 100}%`);
}

/**
 * 把搜索词在描述中标记出来。
 * 调用时机：关键词非空且渲染卡片描述时。
 */
function highlight(text: string): { text: string; hit: boolean }[] {
    const keywordValue = keyword.value.trim();
    if (!keywordValue) return [{ text, hit: false }];
    const parts: { text: string; hit: boolean }[] = [];
    const lower = text.toLowerCase();
    const target = keywordValue.toLowerCase();
    let cursor = 0;
    let index = lower.indexOf(target);
    while (index >= 0) {
        if (index > cursor) parts.push({ text: text.slice(cursor, index), hit: false });
        parts.push({ text: text.slice(index, index + target.length), hit: true });
        cursor = index + target.length;
        index = lower.indexOf(target, cursor);
    }
    if (cursor < text.length) parts.push({ text: text.slice(cursor), hit: false });
    return parts;
}

/**
 * 格式化文件体积。
 * 调用时机：渲染卡片元信息时。
 */
function formatSize(bytes: number): string {
    if (!bytes) return "—";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

/**
 * 格式化日期。
 * 调用时机：渲染卡片更新时间时。
 */
function formatDate(value: string): string {
    return new Date(value).toLocaleDateString("zh-CN", { month: "2-digit", day: "2-digit" });
}
</script>

<style scoped>
.halo-input {
    transition:
        box-shadow 0.35s ease,
        border-color 0.2s ease;
}

.halo-wrap:focus-within .halo-input {
    border-color: rgba(201, 80, 44, 0.45);
    box-shadow:
        0 0 0 3px rgba(201, 80, 44, 0.08),
        0 0 34px rgba(201, 80, 44, 0.16);
}

.halo-wrap::after {
    content: "";
    position: absolute;
    inset: -1px;
    border-radius: 13px;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.35s ease;
    background: radial-gradient(60% 120% at 50% 50%, rgba(201, 80, 44, 0.12), transparent 70%);
}

.halo-wrap:focus-within::after {
    opacity: 1;
}

.shimmer-tile {
    background-image: linear-gradient(110deg, transparent 30%, rgba(255, 255, 255, 0.65) 46%, transparent 62%);
    background-size: 260% 100%;
    background-position: 140% 0;
    background-repeat: no-repeat;
    transition:
        background-position 0.9s ease,
        border-color 0.2s ease,
        transform 0.2s ease,
        color 0.2s ease;
}

.shimmer-tile:hover {
    background-position: -60% 0;
}

.glare {
    position: absolute;
    inset: 0;
    z-index: 0;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.3s ease;
    background-image: linear-gradient(
        var(--gx, 115deg),
        transparent 32%,
        rgba(255, 255, 255, 0.34) 46%,
        rgba(96, 112, 136, 0.05) 52%,
        transparent 70%
    );
    background-size: 260% 260%;
    background-position: var(--px, 50%) var(--py, 50%);
}

.group:hover .glare {
    opacity: 1;
}
</style>
