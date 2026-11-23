<template>
    <div class="border-beam" :style="variables" />
</template>

<script setup lang="ts">
/**
 * 边框流光（改编自 Inspira UI 的 Border Beam）。
 * 调用时机：卡片 hover 时沿边框掠过一次循环，未 hover 时不绘制也不耗帧。
 */
import { computed } from "vue";

const props = withDefaults(
    defineProps<{
        duration?: number;
        delay?: number;
        borderWidth?: number;
        colorFrom?: string;
        colorTo?: string;
    }>(),
    {
        duration: 4.5,
        delay: 0,
        borderWidth: 1.2,
        colorFrom: "#121316",
        colorTo: "#9aa3ae",
    },
);

const variables = computed(() => ({
    "--beam-duration": `${props.duration}s`,
    "--beam-delay": `${props.delay}s`,
    "--beam-border": `${props.borderWidth}px`,
    "--beam-from": props.colorFrom,
    "--beam-to": props.colorTo,
}));
</script>

<style scoped>
.border-beam {
    position: absolute;
    inset: 0;
    padding: var(--beam-border);
    pointer-events: none;
    overflow: hidden;
    -webkit-mask:
        linear-gradient(#000 0 0) content-box,
        linear-gradient(#000 0 0);
    -webkit-mask-composite: xor;
    mask:
        linear-gradient(#000 0 0) content-box,
        linear-gradient(#000 0 0);
    mask-composite: exclude;
}

.border-beam::before {
    content: "";
    position: absolute;
    left: 50%;
    top: 50%;
    width: 220%;
    aspect-ratio: 1;
    background: conic-gradient(
        from 0deg,
        transparent 0deg 44deg,
        var(--beam-from) 66deg,
        var(--beam-to) 80deg,
        transparent 96deg
    );
    animation: beam-spin var(--beam-duration) linear infinite;
    animation-delay: var(--beam-delay);
}

@keyframes beam-spin {
    from {
        transform: translate(-50%, -50%) rotate(0deg);
    }
    to {
        transform: translate(-50%, -50%) rotate(360deg);
    }
}
</style>
