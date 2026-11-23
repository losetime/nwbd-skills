<template>
    <div class="mx-auto max-w-xl pt-14">
        <p class="text-[11px] font-medium tracking-[0.18em] text-ink-faint uppercase">Upload</p>
        <h1 class="mt-3 font-display text-[30px] leading-tight tracking-tight text-ink">上传技能</h1>
        <p class="mt-2 text-[13px] leading-6 text-ink-soft">打包成 zip，包内需要一份 SKILL.md。上传后先成为草稿，确认无误再发布。</p>

        <label
            class="mt-8 flex cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed px-6 py-16 text-center transition"
            :class="dragging ? 'border-accent bg-accent-soft/40' : 'border-line bg-white/60 hover:border-ink/25 hover:bg-white'"
            @dragover.prevent="dragging = true"
            @dragleave.prevent="dragging = false"
            @drop.prevent="onDrop"
        >
            <input type="file" accept=".zip" class="hidden" @change="onPick" />
            <div class="flex h-11 w-11 items-center justify-center rounded-xl bg-paper-deep text-ink-soft">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
                    <path d="M12 16V4m0 0L7 9m5-5 5 5" />
                    <path d="M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3" />
                </svg>
            </div>
            <p class="mt-4 text-[13.5px] font-medium text-ink">{{ file ? file.name : "拖入 zip，或点击选择" }}</p>
            <p class="mt-1 text-[12px] text-ink-faint">{{ file ? formatSize(file.size) : "单包不超过 50 MB，包内不超过 500 个文件" }}</p>
        </label>

        <div class="mt-4">
            <label class="label">变更说明</label>
            <textarea v-model="changelog" rows="3" class="field resize-none" placeholder="这次是什么内容，首次上传可留空"></textarea>
        </div>

        <div v-if="errors.length" class="mt-4 rounded-xl border border-accent/25 bg-accent-soft/50 px-4 py-3">
            <p class="text-[12px] font-medium text-accent">校验未通过</p>
            <ul class="mt-1.5 space-y-1">
                <li v-for="(item, index) in errors" :key="index" class="text-[11.5px] leading-5 text-ink-soft">
                    <span class="font-mono text-[10.5px] text-accent">{{ item.field }}</span>
                    <span class="mx-1.5 text-line">·</span>{{ item.message }}
                </li>
            </ul>
        </div>

        <div class="mt-6 flex items-center justify-between">
            <router-link to="/" class="text-[12px] text-ink-faint transition hover:text-ink">返回技能库</router-link>
            <button class="btn-solid" :disabled="!file || loading" @click="submit">
                {{ loading ? "上传中…" : "上传" }}
            </button>
        </div>

        <div class="mt-12 rounded-xl border border-line bg-white/50 px-5 py-4">
            <p class="mb-2 text-[11px] font-medium tracking-[0.08em] text-ink-faint uppercase">包结构</p>
            <pre class="font-mono text-[11.5px] leading-6 text-ink-soft">my-skill/
├── SKILL.md          # 必须，含 name 与 description
├── references/       # 可选，按需加载的参考
└── scripts/          # 可选，辅助脚本</pre>
        </div>

        <MultiStepLoader :open="loading" :steps="steps" :current="step" hint="正在校验技能包" />
    </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";

import { ApiError } from "@/@api/http";
import { uploadSkill } from "@/@api/skills";
import MultiStepLoader from "@/components/inspira/MultiStepLoader.vue";

defineOptions({ name: "SkillUploadPage" });

const router = useRouter();
const file = ref<File | null>(null);
const changelog = ref("");
const dragging = ref(false);
const loading = ref(false);
const errors = ref<{ field: string; message: string }[]>([]);
const step = ref(0);
const steps = ["读取文件", "校验结构", "解包存储", "写入记录"];

/**
 * 选择本地文件。
 * 调用时机：点击上传区域并确认文件后。
 */
function onPick(event: Event) {
    const target = event.target as HTMLInputElement;
    if (target.files?.length) {
        file.value = target.files[0];
        errors.value = [];
    }
}

/**
 * 处理拖拽投放。
 * 调用时机：文件被拖入并释放到上传区域时。
 */
function onDrop(event: DragEvent) {
    dragging.value = false;
    const dropped = event.dataTransfer?.files?.[0];
    if (!dropped) return;
    if (!dropped.name.endsWith(".zip")) {
        errors.value = [{ field: "package", message: "只接受 zip 文件" }];
        return;
    }
    file.value = dropped;
    errors.value = [];
}

/**
 * 提交上传。
 * 调用时机：点击上传按钮时；失败时逐条展示后端校验原因。
 */
async function submit() {
    if (!file.value) return;
    loading.value = true;
    errors.value = [];
    step.value = 0;

    // 步骤推进只用于反馈，真实校验由后端一次完成
    const timer = setInterval(() => {
        if (step.value < 2) step.value += 1;
    }, 620);

    try {
        const result = await uploadSkill(file.value, changelog.value);
        step.value = 3;
        await new Promise((resolve) => setTimeout(resolve, 320));
        await router.push({ name: "skill-detail", params: { name: result.name } });
    } catch (err) {
        if (err instanceof ApiError) {
            errors.value = err.details.length ? err.details : [{ field: "package", message: err.message }];
        } else {
            errors.value = [{ field: "package", message: "上传失败，请稍后重试" }];
        }
    } finally {
        clearInterval(timer);
        loading.value = false;
    }
}

/**
 * 格式化体积。
 * 调用时机：显示已选文件信息时。
 */
function formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
</script>
