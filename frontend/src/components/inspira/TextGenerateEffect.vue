<template>
    <component :is="tag" ref="scope" class="inline-block">
        <span
            v-for="(unit, index) in units"
            :key="`${unit}-${index}`"
            class="inline-block whitespace-pre"
            :style="unitStyle(index)"
        >{{ unit }}</span>
    </component>
</template>

<script setup lang="ts">
/**
 * 文字逐字渐显（改编自 Inspira UI 的 Text Generate Effect）。
 * 调用时机：首屏标题挂载时播放一次，不做循环。
 */
import { computed, onMounted, ref } from "vue";

const props = withDefaults(
    defineProps<{
        text: string;
        tag?: string;
        duration?: number;
        delay?: number;
        stagger?: number;
        split?: "char" | "word";
    }>(),
    { tag: "h1", duration: 0.6, delay: 80, stagger: 90, split: "char" },
);

const scope = ref<HTMLElement | null>(null);
const played = ref(false);

const units = computed(() => {
    if (props.split === "word") {
        return props.text.split(" ").map((word, index, all) => (index < all.length - 1 ? `${word} ` : word));
    }
    return Array.from(props.text);
});

/**
 * 单个字符的初始样式，挂载后由脚本去除模糊与透明。
 * 调用时机：渲染每个字符时。
 */
function unitStyle(index: number) {
    if (played.value) return {};
    return {
        opacity: "0",
        filter: "blur(8px)",
        transform: "translateY(0.18em)",
        transition: `opacity ${props.duration}s ease, filter ${props.duration}s ease, transform ${props.duration}s cubic-bezier(0.22,1,0.36,1)`,
        transitionDelay: `${props.delay + index * props.stagger}ms`,
    };
}

onMounted(() => {
    const element = scope.value;
    if (!element) return;
    const spans = Array.from(element.querySelectorAll("span"));
    requestAnimationFrame(() => {
        spans.forEach((span, index) => {
            const target = span as HTMLElement;
            target.style.transitionDelay = `${props.delay + index * props.stagger}ms`;
            target.style.opacity = "1";
            target.style.filter = "blur(0px)";
            target.style.transform = "translateY(0)";
        });
    });
});
</script>
