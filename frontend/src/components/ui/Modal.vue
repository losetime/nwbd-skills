<template>
    <Teleport to="body">
        <Transition name="modal" :duration="{ enter: 480, leave: 220 }">
            <div v-if="open" class="fixed inset-0 flex items-center justify-center p-6" :style="{ zIndex }" @click.self="emit('close')">
                <div class="modal-overlay absolute inset-0 bg-ink/25 backdrop-blur-[6px]" />
                <div class="modal-panel relative w-full" :class="width" role="dialog" aria-modal="true">
                    <slot />
                </div>
            </div>
        </Transition>
    </Teleport>
</template>

<script setup lang="ts">
/**
 * 弹窗容器（动画取自 Inspira UI 的 Animated Modal，用 CSS 3D 实现）。
 * 调用时机：需要浮层交互时包裹内容；打开时锁定页面滚动，关闭后恢复。
 */
import { onBeforeUnmount, watch } from "vue";

const props = withDefaults(defineProps<{ open: boolean; width?: string; zIndex?: number }>(), {
    width: "max-w-md",
    zIndex: 100,
});

const emit = defineEmits<{ close: [] }>();

// 允许多层弹窗叠加时只加锁一次
let lockCount = 0;
let previousOverflow = "";
let previousPadding = "";
let rootOverflow = "";

/**
 * 锁定或解除页面滚动。
 * 调用时机：弹窗打开状态变化时。
 */
function setScrollLocked(locked: boolean) {
    if (typeof document === "undefined") return;
    const root = document.documentElement;
    if (locked) {
        if (lockCount === 0) {
            previousOverflow = document.body.style.overflow;
            previousPadding = document.body.style.paddingRight;
            rootOverflow = root.style.overflow;
            // 滚动发生在 documentElement 上，body 也要一起锁
            const gap = window.innerWidth - root.clientWidth;
            root.style.overflow = "hidden";
            document.body.style.overflow = "hidden";
            if (gap > 0) document.body.style.paddingRight = `${gap}px`;
        }
        lockCount += 1;
        return;
    }
    lockCount = Math.max(0, lockCount - 1);
    if (lockCount === 0) {
        root.style.overflow = rootOverflow;
        document.body.style.overflow = previousOverflow;
        document.body.style.paddingRight = previousPadding;
    }
}

watch(
    () => props.open,
    (open) => setScrollLocked(Boolean(open)),
    { immediate: true },
);

onBeforeUnmount(() => {
    if (props.open) setScrollLocked(false);
});
</script>

<style scoped>
/* 用 CSS 动画而不是过渡类：即使浏览器暂停了 rAF，动画也能走完并停在终态 */
.modal-panel {
    transform-origin: 50% 55%;
    animation: panel-in 0.48s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}

.modal-overlay {
    animation: overlay-in 0.3s ease both;
}

.modal-leave-active .modal-panel {
    animation: panel-out 0.22s ease both;
}

.modal-leave-active .modal-overlay {
    animation: overlay-out 0.22s ease both;
}

@keyframes panel-in {
    from {
        opacity: 0;
        transform: perspective(1400px) rotateX(80deg) scale(0.55) translateY(40px);
    }
    to {
        opacity: 1;
        transform: perspective(1400px) rotateX(0deg) scale(1) translateY(0);
    }
}

@keyframes panel-out {
    from {
        opacity: 1;
        transform: perspective(1400px) rotateX(0deg) scale(1);
    }
    to {
        opacity: 0;
        transform: perspective(1400px) rotateX(12deg) scale(0.85);
    }
}

@keyframes overlay-in {
    from {
        opacity: 0;
    }
    to {
        opacity: 1;
    }
}

@keyframes overlay-out {
    from {
        opacity: 1;
    }
    to {
        opacity: 0;
    }
}
</style>
