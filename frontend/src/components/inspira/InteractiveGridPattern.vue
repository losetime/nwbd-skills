<template>
    <div ref="element" class="grid-layer" :style="style" />
</template>

<script setup lang="ts">
/**
 * 交互网格（改编自 Inspira UI 的 Interactive Grid Pattern）。
 * 调用时机：首屏背景；鼠标移动时网格整体向光标方向轻微偏移，形成跟随感。
 */
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

const props = withDefaults(defineProps<{ size?: number; shift?: number }>(), { size: 40, shift: 6 });

const element = ref<HTMLElement | null>(null);
const offset = ref({ x: 0, y: 0 });

/**
 * 依据鼠标位置计算网格偏移。
 * 调用时机：窗口内鼠标移动时。
 */
function track(event: MouseEvent) {
    const rect = element.value?.getBoundingClientRect();
    if (!rect) return;
    const ratioX = (event.clientX - rect.left) / Math.max(rect.width, 1) - 0.5;
    const ratioY = (event.clientY - rect.top) / Math.max(rect.height, 1) - 0.5;
    offset.value = {
        x: -ratioX * props.shift,
        y: -ratioY * props.shift,
    };
}

onMounted(() => window.addEventListener("mousemove", track, { passive: true }));
onBeforeUnmount(() => window.removeEventListener("mousemove", track));

const style = computed(() => ({
    backgroundSize: `${props.size}px ${props.size}px`,
    backgroundPosition: `${offset.value.x}px ${offset.value.y}px`,
}));
</script>

<style scoped>
.grid-layer {
    position: absolute;
    inset: 0;
    pointer-events: none;
    background-image:
        linear-gradient(to right, rgba(18, 19, 22, 0.20) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(18, 19, 22, 0.20) 1px, transparent 1px);
    transition: background-position 0.25s ease-out;
}
</style>
