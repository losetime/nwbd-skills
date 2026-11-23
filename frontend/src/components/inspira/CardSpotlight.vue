<template>
    <div
        class="group relative rounded-[inherit]"
        @mousemove="move"
        @mouseleave="reset"
    >
        <slot />
        <div class="pointer-events-none absolute inset-0 rounded-[inherit] opacity-0 transition-opacity duration-300 group-hover:opacity-100" :style="overlay" />
    </div>
</template>

<script setup lang="ts">
/**
 * 卡片聚光（改编自 Inspira UI 的 Card Spotlight）。
 * 调用时机：鼠标在卡片内移动时更新光斑位置，移出后归位。
 */
import { computed, ref } from "vue";

const props = withDefaults(
    defineProps<{
        size?: number;
        color?: string;
        opacity?: number;
    }>(),
    { size: 260, color: "rgba(96, 112, 136, 0.14)", opacity: 1 },
);

const x = ref(-999);
const y = ref(-999);

/**
 * 更新光斑坐标。
 * 调用时机：监听到卡片内鼠标移动时。
 */
function move(event: MouseEvent) {
    const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
    x.value = event.clientX - rect.left;
    y.value = event.clientY - rect.top;
}

/**
 * 把光斑移出可视区域。
 * 调用时机：鼠标离开卡片时。
 */
function reset() {
    x.value = -999;
    y.value = -999;
}

const overlay = computed(() => ({
    background: `radial-gradient(${props.size}px circle at ${x.value}px ${y.value}px, ${props.color}, transparent 65%)`,
    opacity: String(props.opacity),
}));
</script>
