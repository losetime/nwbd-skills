<template>
    <span class="relative inline-grid overflow-hidden align-bottom">
        <span
            v-for="(word, index) in words"
            :key="word"
            class="col-start-1 row-start-1 whitespace-nowrap transition-all duration-500"
            :class="index === current ? 'translate-y-0 opacity-100 blur-0' : index < current ? '-translate-y-6 opacity-0 blur-[2px]' : 'translate-y-6 opacity-0 blur-[2px]'"
        >{{ word }}</span>
        <!-- 占位，撑开最宽的一项 -->
        <span class="invisible col-start-1 row-start-1 whitespace-nowrap">{{ widest }}</span>
    </span>
</template>

<script setup lang="ts">
/**
 * 词语翻转（改编自 Inspira UI 的 Flip Words）。
 * 调用时机：登录页陈述句中的轮换词，按固定间隔切换。
 */
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

const props = withDefaults(defineProps<{ words: string[]; interval?: number }>(), { interval: 2600 });

const current = ref(0);
let timer: ReturnType<typeof setInterval> | undefined;

const widest = computed(() => props.words.reduce((longest, word) => (word.length > longest.length ? word : longest), ""));

onMounted(() => {
    timer = setInterval(() => {
        current.value = (current.value + 1) % props.words.length;
    }, props.interval);
});

onBeforeUnmount(() => clearInterval(timer));
</script>
