<template>
    <ul class="space-y-0.5">
        <li v-for="node in nodes" :key="node.path">
            <div
                v-if="node.children.length"
                class="flex w-full items-center gap-1.5 rounded-lg px-2 py-1.5 text-left font-mono text-[11.5px] text-ink-soft transition-colors hover:bg-white/70"
                role="button"
                tabindex="0"
                @click="toggle(node.path)"
                @keydown.enter="toggle(node.path)"
            >
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" class="transition-transform duration-200" :class="collapsed.has(node.path) ? '' : 'rotate-90'">
                    <path d="m9 6 6 6-6 6" />
                </svg>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
                    <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z" />
                </svg>
                <span class="truncate">{{ node.name }}</span>
                <span class="ml-auto text-[10px] text-ink-faint">{{ node.children.length }}</span>
            </div>

            <button
                v-else
                class="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left font-mono text-[11.5px] transition-colors"
                :class="node.path === selected ? 'bg-white text-ink' : 'text-ink-soft hover:bg-white/70'"
                @click="emit('select', node.path)"
            >
                <span class="w-2.5" />
                <span class="min-w-0 flex-1 truncate">{{ node.name }}</span>
                <span class="shrink-0 text-[10px] text-ink-faint">{{ formatSize(node.size) }}</span>
            </button>

            <div v-if="node.children.length && !collapsed.has(node.path)" class="ml-3 border-l border-line/70 pl-2">
                <FileTree :nodes="node.children" :selected="selected" @select="(path) => emit('select', path)" />
            </div>
        </li>
    </ul>
</template>

<script setup lang="ts">
/**
 * 文件树（改编自 Inspira UI 的 File Tree）。
 * 调用时机：详情页展示包内目录结构，支持文件夹折叠与文件选择。
 */
import { ref } from "vue";

import type { TreeNode } from "@/utils/tree";

const props = defineProps<{ nodes: TreeNode[]; selected: string }>();
const emit = defineEmits<{ select: [path: string] }>();

const collapsed = ref<Set<string>>(new Set());

/**
 * 折叠或展开文件夹。
 * 调用时机：点击文件夹行时。
 */
function toggle(path: string) {
    const next = new Set(collapsed.value);
    if (next.has(path)) next.delete(path);
    else next.add(path);
    collapsed.value = next;
}

/**
 * 格式化体积。
 * 调用时机：渲染文件行时。
 */
function formatSize(bytes: number): string {
    if (!bytes) return "";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
</script>
