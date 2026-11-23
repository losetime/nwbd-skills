<template>
    <div v-if="open" class="fixed inset-0 z-50 flex flex-col items-center justify-center bg-paper/85 backdrop-blur-md">
        <div class="relative flex h-14 w-14 items-center justify-center">
            <span class="absolute inset-0 border border-line" />
            <svg class="spinner absolute inset-0 h-full w-full" viewBox="0 0 56 56">
                <circle cx="28" cy="28" r="27" fill="none" stroke="var(--color-accent)" stroke-width="1.6" stroke-linecap="butt" stroke-dasharray="38 132" />
            </svg>
            <span class="font-mono text-[11px] text-ink-soft">{{ String(current + 1).padStart(2, "0") }}</span>
        </div>

        <ul class="mt-7 w-64 space-y-3">
            <li v-for="(step, index) in steps" :key="step" class="flex items-center gap-3 text-[13px]">
                <span
                    class="flex h-4 w-4 items-center justify-center rounded-full border transition-colors duration-300"
                    :class="index < current ? 'border-ink bg-ink text-white' : index === current ? 'border-accent text-accent' : 'border-line text-transparent'"
                >
                    <svg v-if="index < current" width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.5">
                        <path d="m5 13 4 4L19 7" />
                    </svg>
                    <span v-else class="h-1 w-1 rounded-full" :class="index === current ? 'bg-accent' : 'bg-line'" />
                </span>
                <span :class="index <= current ? 'text-ink' : 'text-ink-faint'">{{ step }}</span>
            </li>
        </ul>

        <p class="mt-8 text-[11px] tracking-[0.16em] text-ink-faint uppercase">{{ hint }}</p>
    </div>
</template>

<script setup lang="ts">
/**
 * 多步加载（改编自 Inspira UI 的 Multi Step Loader）。
 * 调用时机：上传与校验过程中覆盖全屏展示，步骤与后端处理阶段对应。
 */
withDefaults(defineProps<{ open: boolean; steps: string[]; current: number; hint?: string }>(), { hint: "处理中" });
</script>

<style scoped>
.spinner {
    animation: spin 0.9s linear infinite;
    transform-origin: center;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}
</style>
