<template>
    <span class="inline-block tabular-nums">{{ output }}</span>
</template>

<script setup lang="ts">
/**
 * 数字滚动（改编自 Inspira UI 的 Number Ticker）。
 * 调用时机：组件挂载后从 0 缓动到目标值，目标值变化时从当前值继续缓动。
 */
import { computed, onBeforeUnmount, ref, watch } from "vue";

const props = withDefaults(
    defineProps<{
        value: number;
        duration?: number;
        delay?: number;
        decimals?: number;
    }>(),
    { duration: 900, delay: 0, decimals: 0 },
);

const current = ref(0);
let frame = 0;

/** easeOutCubic，让数字先快后慢地停下。 */
function easeOutCubic(t: number): number {
    return 1 - (1 - t) ** 3;
}

/**
 * 从当前值缓动到目标值。
 * 调用时机：首次挂载与目标值变化时调用。
 */
function animateTo(target: number) {
    cancelAnimationFrame(frame);
    clearTimeout(settle);
    const from = current.value;
    const start = performance.now();
    const tick = (now: number) => {
        const progress = Math.min((now - start) / Math.max(props.duration, 1), 1);
        current.value = from + (target - from) * easeOutCubic(progress);
        if (progress < 1) frame = requestAnimationFrame(tick);
        else current.value = target;
    };
    frame = requestAnimationFrame(tick);
    // 标签页在后台时 rAF 会被暂停，用定时器兜底保证最终值正确
    settle = setTimeout(() => {
        current.value = target;
    }, props.duration + 120);
}

let settle: ReturnType<typeof setTimeout> | undefined;

watch(
    () => props.value,
    (target) => {
        if (props.delay > 0 && current.value === 0) {
            setTimeout(() => animateTo(target), props.delay);
            return;
        }
        animateTo(target);
    },
    { immediate: true },
);

onBeforeUnmount(() => {
    cancelAnimationFrame(frame);
    clearTimeout(settle);
});

const output = computed(() =>
    new Intl.NumberFormat("en-US", {
        minimumFractionDigits: props.decimals,
        maximumFractionDigits: props.decimals,
    }).format(Number(current.value.toFixed(props.decimals))),
);
</script>
