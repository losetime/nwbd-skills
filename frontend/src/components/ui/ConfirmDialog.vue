<template>
    <Modal :open="open" width="max-w-sm" :z-index="300" @close="emit('cancel')">
        <div class="border border-line bg-white p-6">
            <h3 class="font-display text-[17px] text-ink">{{ title }}</h3>
            <p class="mt-2 text-[12.5px] leading-6 text-ink-soft">{{ message }}</p>
            <div class="mt-5 flex justify-end gap-2">
                <button class="btn-ghost" @click="emit('cancel')">取消</button>
                <button
                    class="btn-solid"
                    :class="toneClass"
                    :disabled="busy"
                    @click="emit('confirm')"
                >
                    {{ busy ? "处理中…" : confirmLabel }}
                </button>
            </div>
        </div>
    </Modal>
</template>

<script setup lang="ts">
/**
 * 确认弹窗。
 * 调用时机：需要用户二次确认的操作，替代浏览器原生 confirm。
 */
import { computed } from "vue";

import Modal from "@/components/ui/Modal.vue";

const props = withDefaults(
    defineProps<{
        open: boolean;
        title: string;
        message: string;
        confirmLabel?: string;
        tone?: "default" | "danger" | "warning";
        busy?: boolean;
    }>(),
    { confirmLabel: "确认", tone: "default", busy: false },
);

const emit = defineEmits<{ confirm: []; cancel: [] }>();

/** 确认按钮配色：普通为墨色，警告为琥珀色，危险为赭红。 */
const toneClass = computed(() => {
    if (props.tone === "danger") return "bg-accent hover:bg-accent/90";
    if (props.tone === "warning") return "bg-amber-600 hover:bg-amber-700";
    return "";
});
</script>
