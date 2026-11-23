<template>
    <div class="pt-8">
        <router-link to="/" class="inline-flex items-center gap-1.5 text-[12px] text-ink-faint transition hover:text-ink">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path d="M15 18l-6-6 6-6" />
            </svg>
            全部技能
        </router-link>

        <div v-if="detail" class="mt-4 flex flex-wrap items-start justify-between gap-6 border-b border-line pb-7">
            <div class="min-w-0">
                <div class="flex items-center gap-2.5">
                    <span class="flex h-9 w-9 items-center justify-center rounded-xl font-display text-[14px] text-white/95" :style="glyph(detail.name)">
                        {{ detail.name.slice(0, 1).toUpperCase() }}
                    </span>
                    <h1 class="font-display text-[30px] leading-none tracking-tight text-ink">{{ detail.name }}</h1>
                </div>
                <p class="mt-3 max-w-2xl text-[13.5px] leading-6 text-ink-soft">{{ detail.summary || "暂无描述" }}</p>
                <div class="mt-4 flex flex-wrap items-center gap-2 text-[11px] text-ink-faint">
                    <span class="chip">当前 v{{ detail.current_version ?? "—" }}</span>
                    <span class="chip">{{ files.length }} 个文件</span>
                    <span class="chip">{{ formatSize(selectedVersionInfo?.size_bytes ?? 0) }}</span>
                    <span class="chip">更新于 {{ formatDate(detail.updated_at) }}</span>
                </div>
            </div>
            <div class="flex shrink-0 items-center gap-2">
                <a v-if="detail" :href="downloadUrl(detail.name, selectedVersion)" class="btn-quiet">下载 zip</a>
                <button v-if="canManage" class="btn-solid" @click="openUpload">上传新版本</button>
                <button v-if="auth.isAdmin" class="btn-quiet" @click="openTransfer">转移</button>
                <button
                    v-if="canDelete"
                    class="inline-flex h-[37px] w-[37px] items-center justify-center border border-line bg-white text-ink-faint transition hover:border-accent/40 hover:text-accent"
                    title="删除技能"
                    @click="showDelete = true"
                >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">
                        <path d="M4 7h16M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2M6 7l1 13a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1l1-13" />
                        <path d="M10 11v6M14 11v6" />
                    </svg>
                </button>
            </div>
        </div>

        <div v-if="detail" class="mt-8 grid gap-10 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
            <!-- 阅读区 -->
            <article class="min-w-0 lg:min-h-[560px]">
                <div class="flex items-center justify-between border-b border-line pb-3">
                    <span class="font-mono text-[11px] text-ink-faint">{{ activePath || "—" }}</span>
                    <button v-if="content" class="inline-flex items-center gap-1.5 border border-line bg-white px-2.5 py-1 text-[11px] text-ink-soft transition hover:border-ink/30 hover:text-ink" @click="copy">
                        <svg v-if="!copied" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                            <rect x="9" y="9" width="11" height="11" />
                            <path d="M5 15V5a1 1 0 0 1 1-1h9" />
                        </svg>
                        <svg v-else width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4">
                            <path d="m5 13 4 4L19 7" />
                        </svg>
                        {{ copied ? "已复制" : "复制" }}
                    </button>
                </div>

                <div v-if="isSkillMd && blocks.length" class="pt-6 transition-opacity" :class="{ 'opacity-40': previewLoading }">
                    <dl v-if="meta.length" class="mb-7 grid gap-x-6 gap-y-2 rounded-xl border border-line bg-white/60 px-4 py-3 sm:grid-cols-[88px_1fr]">
                        <template v-for="entry in meta" :key="entry.key">
                            <dt class="font-mono text-[11px] text-ink-faint">{{ entry.key }}</dt>
                            <dd class="text-[12.5px] leading-6 text-ink-soft">{{ entry.value }}</dd>
                        </template>
                    </dl>

                    <template v-for="(block, index) in blocks" :key="index">
                        <h2 v-if="block.kind === 'h1'" class="mt-8 mb-3 font-display text-[22px] tracking-tight text-ink first:mt-0">{{ block.text }}</h2>
                        <h3 v-else-if="block.kind === 'h2'" class="mt-7 mb-2.5 font-display text-[17px] text-ink">{{ block.text }}</h3>
                        <h4 v-else-if="block.kind === 'h3'" class="mt-6 mb-2 text-[13px] font-semibold tracking-wide text-ink">{{ block.text }}</h4>
                        <p v-else-if="block.kind === 'p'" class="mb-3.5 text-[14px] leading-[1.85] text-ink-soft">{{ block.text }}</p>
                        <div v-else-if="block.kind === 'li'" class="mb-1.5 flex gap-2.5 text-[14px] leading-[1.85] text-ink-soft">
                            <span class="mt-2.5 h-1 w-1 shrink-0 rounded-full bg-ink-faint"></span>
                            <span>{{ block.text }}</span>
                        </div>
                        <blockquote v-else-if="block.kind === 'quote'" class="my-4 border-l-2 border-accent/40 pl-4 text-[13px] leading-7 text-ink-soft italic">
                            {{ block.text }}
                        </blockquote>
                        <pre v-else-if="block.kind === 'code'" class="my-4 overflow-x-auto rounded-xl bg-ink px-4 py-3 font-mono text-[12px] leading-6 text-white/85">{{ block.text }}</pre>
                        <hr v-else-if="block.kind === 'hr'" class="my-7 border-line" />
                    </template>
                </div>

                <pre v-else-if="content" class="whitespace-pre-wrap break-words pt-6 font-mono text-[12.5px] leading-7 text-ink-soft transition-opacity" :class="{ 'opacity-40': previewLoading }">{{ content }}</pre>
                <p v-else class="py-16 text-center text-[13px] text-ink-faint">这个版本还没有可预览的文件</p>
            </article>

            <!-- 右侧信息栏 -->
            <aside class="min-w-0 space-y-8 lg:sticky lg:top-24 lg:self-start">
                <section>
                    <div class="mb-3 flex items-baseline justify-between">
                        <h2 class="text-[11px] font-medium tracking-[0.1em] text-ink-faint uppercase">版本</h2>
                        <span class="font-mono text-[10.5px] text-ink-faint">{{ detail.versions.length }} 个</span>
                    </div>

                    <ul class="space-y-1 pb-1">
                        <li v-for="version in visibleVersions" :key="version.version">
                            <button
                                class="block w-full min-w-0 border-l-2 px-4 py-3 text-left transition-colors"
                                :class="[
                                    version.version === detail.current_version ? 'border-emerald-600' : version.version === selectedVersion ? 'border-ink/40' : 'border-transparent',
                                    version.version === selectedVersion ? 'bg-white' : 'hover:bg-white/60',
                                ]"
                                @click="selectVersion(version.version)"
                            >
                                <span class="flex items-baseline gap-2">
                                    <span class="font-mono text-[12.5px]" :class="version.version === selectedVersion ? 'font-semibold text-ink' : 'text-ink-soft'">v{{ version.version }}</span>
                                    <span class="text-[10px] font-medium tracking-wide uppercase" :class="kindClass(versionKind(version))">{{ kindLabel(versionKind(version)) }}</span>
                                    <span class="ml-auto font-mono text-[10.5px] tabular-nums text-ink-faint">{{ formatDate(version.created_at) }}</span>
                                </span>
                                <span class="mt-0.5 block whitespace-normal break-words text-[11.5px] leading-5" :class="version.version === selectedVersion ? 'text-ink-soft' : 'text-ink-faint'">{{ version.changelog || "无变更说明" }}</span>
                            </button>
                        </li>
                    </ul>
                    <p v-if="!mainVersions.length" class="border border-dashed border-line px-3 py-6 text-center text-[11.5px] text-ink-faint">
                        还没有发布过版本
                    </p>

                    <button
                        v-if="hasOtherVersions"
                        class="mt-2 w-full border border-line bg-white py-1.5 text-[11.5px] text-ink-soft transition hover:border-ink/30 hover:text-ink"
                        @click="openAllVersions"
                    >
                        查看全部 {{ detail.versions.length }} 个版本
                    </button>

                    <div v-if="selectedVersion" class="mt-4 flex flex-wrap gap-1.5">
                        <button v-if="canPublish" class="btn-quiet px-3 py-1 text-[11.5px]" @click="requestPublish()">
                            {{ selectedVersionInfo?.status === "draft" ? "发布" : "设为当前" }}
                        </button>
                        <button v-if="canDeprecate" class="btn-ghost px-3 py-1 text-[11.5px] text-accent" @click="requestDeprecate()">
                            废弃
                        </button>
                        <span v-if="selectedKind === 'current'" class="text-[11px] text-ink-faint">该版本正在对外提供下载</span>
                        <router-link v-if="!auth.isLoggedIn" :to="{ name: 'login', query: { redirect: route.fullPath } }" class="text-[11px] text-ink-faint underline-offset-2 transition hover:text-ink hover:underline">
                            登录后可管理版本
                        </router-link>
                        <span v-else-if="!canManage" class="text-[11px] text-ink-faint">该技能由其他账号创建，仅创建者可管理</span>
                    </div>
                </section>

                <section>
                    <div class="mb-3 flex items-baseline justify-between">
                        <h2 class="text-[11px] font-medium tracking-[0.1em] text-ink-faint uppercase">文件</h2>
                        <span class="font-mono text-[10.5px] text-ink-faint">{{ files.length }}</span>
                    </div>
                    <div class="relative">
                        <div class="max-h-[440px] overflow-y-auto pb-4">
                            <FileTree :nodes="fileTree" :selected="activePath" @select="openFile" />
                        </div>
                    </div>
                </section>
            </aside>
        </div>

        <div v-else class="py-24 text-center text-[13px] text-ink-faint">加载中…</div>

        <!-- 右下角浮动操作 -->
        <div class="fixed bottom-7 right-7 z-40 flex flex-col items-end gap-2">
            <button
                class="relative flex h-11 w-11 items-center justify-center border border-line bg-white text-ink-soft transition hover:border-ink/30 hover:text-ink"
                title="评论"
                aria-label="评论"
                @click="openComments"
            >
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">
                    <path d="M20 14.5a3 3 0 0 1-3 3H8l-4 3v-14a3 3 0 0 1 3-3h10a3 3 0 0 1 3 3z" />
                </svg>
                <span
                    v-if="commentTotal"
                    class="absolute -right-1.5 -top-1.5 flex h-4 min-w-4 items-center justify-center border border-line bg-white px-1 font-mono text-[9.5px] tabular-nums text-ink-soft"
                >
                    {{ commentTotal > 99 ? "99+" : commentTotal }}
                </span>
            </button>

            <button
                class="flex h-11 w-11 items-center justify-center border border-line bg-white text-ink-soft transition hover:border-ink/30 hover:text-ink"
                title="安装说明"
                aria-label="安装说明"
                @click="showInstallHelp = true"
            >
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">
                    <circle cx="12" cy="12" r="9" />
                    <path d="M9.6 9.3a2.6 2.6 0 1 1 3.6 2.4c-.7.3-1.2.9-1.2 1.7v.3" />
                    <path d="M12 17h.01" />
                </svg>
            </button>
        </div>

        <Modal :open="showInstallHelp" width="max-w-lg" @close="showInstallHelp = false">
            <div class="max-h-[calc(100vh-3rem)] overflow-y-auto border border-line bg-white p-6">
                <div class="flex items-start justify-between gap-4">
                    <div>
                        <h3 class="font-display text-[18px] text-ink">安装到你的 Agent</h3>
                        <p class="mt-1.5 text-[11.5px] leading-5 text-ink-faint">
                            zip 里已经包含 <span class="font-mono text-ink-soft">{{ detail?.name }}/</span> 顶层目录，解压后把整个目录放进去即可。
                        </p>
                    </div>
                    <button
                        class="flex h-7 w-7 shrink-0 items-center justify-center border border-line text-ink-faint transition hover:border-ink/30 hover:text-ink"
                        title="关闭"
                        aria-label="关闭"
                        @click="showInstallHelp = false"
                    >
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M6 6l12 12M18 6L6 18" />
                        </svg>
                    </button>
                </div>

                <div class="mt-5 space-y-4">
                    <div class="border-t border-line pt-4">
                        <p class="text-[11px] font-medium tracking-[0.08em] text-ink-faint uppercase">Claude Code</p>
                        <p class="mt-1.5 text-[12.5px] leading-6 text-ink-soft">
                            个人 <span class="font-mono text-ink">~/.claude/skills/</span>
                            <span class="mx-1 text-ink-faint">·</span>
                            项目 <span class="font-mono text-ink">.claude/skills/</span>
                        </p>
                        <p class="mt-0.5 text-[11px] text-ink-faint">Windows：<span class="font-mono">%USERPROFILE%\.claude\skills\</span></p>
                    </div>

                    <div class="border-t border-line pt-4">
                        <p class="text-[11px] font-medium tracking-[0.08em] text-ink-faint uppercase">Claude 网页版 / 桌面版</p>
                        <p class="mt-1.5 text-[12.5px] leading-6 text-ink-soft">设置 → Capabilities → Skills，直接上传下载的 zip，不用解压。</p>
                    </div>

                    <div class="border-t border-line pt-4">
                        <p class="text-[11px] font-medium tracking-[0.08em] text-ink-faint uppercase">OpenCode</p>
                        <p class="mt-1.5 text-[12.5px] leading-6 text-ink-soft">
                            全局 <span class="font-mono text-ink">~/.config/opencode/skills/</span>
                            <span class="mx-1 text-ink-faint">·</span>
                            项目 <span class="font-mono text-ink">.opencode/skills/</span>
                        </p>
                        <p class="mt-0.5 text-[11px] text-ink-faint">Windows：<span class="font-mono">%USERPROFILE%\.config\opencode\skills\</span>，OpenCode Desktop 用同一路径。</p>
                    </div>

                    <div class="border-t border-line pt-4">
                        <p class="text-[11px] font-medium tracking-[0.08em] text-ink-faint uppercase">其他桌面端（WorkBuddy 等）</p>
                        <p class="mt-1.5 text-[12.5px] leading-6 text-ink-soft">
                            在客户端设置的「技能 / Skills」里导入这个 zip；没有导入入口的，解压后把
                            <span class="font-mono text-ink">{{ detail?.name }}/</span> 放进它的技能目录。
                        </p>
                    </div>
                </div>

                <p class="mt-5 border-t border-line pt-4 text-[11px] leading-5 text-ink-faint">
                    目录名要和 SKILL.md 里的 name 一致。装好后新开一个会话，直接描述任务，或点名「用 {{ detail?.name }}」。
                </p>

                <div class="mt-4 flex justify-end">
                    <button class="btn-solid" @click="showInstallHelp = false">知道了</button>
                </div>
            </div>
        </Modal>

        <!-- 评论 -->
        <Modal :open="showComments" width="max-w-lg" @close="showComments = false">
            <div class="max-h-[calc(100vh-3rem)] overflow-y-auto border border-line bg-white p-6">
                <div class="flex items-start justify-between gap-4">
                    <div>
                        <h3 class="font-display text-[18px] text-ink">评论</h3>
                        <p class="mt-1 text-[11.5px] text-ink-faint">{{ commentTotal }} 条 · 按时间倒序，只聊这个技能本身。</p>
                    </div>
                    <button
                        class="flex h-7 w-7 shrink-0 items-center justify-center border border-line text-ink-faint transition hover:border-ink/30 hover:text-ink"
                        title="关闭"
                        aria-label="关闭"
                        @click="showComments = false"
                    >
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M6 6l12 12M18 6L6 18" />
                        </svg>
                    </button>
                </div>

                <div v-if="auth.isLoggedIn" class="mt-4">
                    <textarea
                        v-model="commentDraft"
                        rows="3"
                        maxlength="500"
                        class="field resize-none"
                        placeholder="写下使用反馈或改进建议"
                    ></textarea>
                    <div class="mt-2 flex items-center justify-between">
                        <span class="font-mono text-[10.5px]" :class="commentDraft.length > 480 ? 'text-accent' : 'text-ink-faint'">
                            {{ commentDraft.length }} / 500
                        </span>
                        <button class="btn-solid px-4 py-1.5 text-[12px]" :disabled="commentBusy || !commentDraft.trim()" @click="submitComment">
                            {{ commentBusy ? "发送中…" : "发表" }}
                        </button>
                    </div>
                </div>
                <p v-else class="mt-4 border border-dashed border-line px-3 py-4 text-center text-[12px] text-ink-faint">
                    <router-link :to="{ name: 'login', query: { redirect: route.fullPath } }" class="text-ink underline-offset-2 hover:underline">登录</router-link>
                    后可以发表评论，浏览不需要账号。
                </p>

                <div class="mt-5 border-t border-line">
                    <div v-for="item in comments" :key="item.id" class="border-b border-line/70 py-3.5 last:border-0">
                        <div class="flex items-baseline gap-2">
                            <span class="max-w-[220px] truncate text-[12px] text-ink">{{ item.author }}</span>
                            <span class="font-mono text-[10.5px] text-ink-faint">{{ formatDate(item.created_at) }}</span>
                            <button
                                v-if="canRemoveComment(item)"
                                class="ml-auto text-[10.5px] text-ink-faint transition hover:text-accent"
                                @click="pendingCommentDelete = item.id"
                            >
                                删除
                            </button>
                        </div>
                        <p class="mt-1.5 whitespace-pre-wrap break-words text-[12.5px] leading-6 text-ink-soft">{{ item.body }}</p>
                    </div>

                    <p v-if="!comments.length && !commentsLoading" class="py-10 text-center text-[12px] text-ink-faint">还没有评论</p>
                    <p v-if="commentsLoading" class="py-6 text-center text-[12px] text-ink-faint">加载中…</p>
                </div>

                <button
                    v-if="comments.length < commentTotal"
                    class="mt-3 w-full border border-line bg-white py-1.5 text-[11.5px] text-ink-soft transition hover:border-ink/30 hover:text-ink"
                    @click="loadComments(false)"
                >
                    加载更多
                </button>
            </div>
        </Modal>

        <ConfirmDialog
            :open="!!pendingCommentDelete"
            title="删除评论"
            message="删除后无法恢复。"
            confirm-label="删除"
            tone="danger"
            :busy="commentBusy"
            @confirm="confirmDeleteComment"
            @cancel="pendingCommentDelete = null"
        />

        <!-- 复制提示 -->
        <transition name="toast">
            <div v-if="toast" class="fixed bottom-8 left-1/2 z-50 -translate-x-1/2 border border-ink bg-ink px-4 py-2 text-[12px] text-white">
                {{ toast }}
            </div>
        </transition>

        <!-- 上传新版本 -->
        <Modal :open="showUpload" width="max-w-md" @close="showUpload = false">
            <div class="border border-line bg-white p-6">
                <h3 class="font-display text-[18px] text-ink">上传新版本</h3>
                <p class="mt-1 text-[12px] text-ink-faint">包内 SKILL.md 的 name 必须与 {{ detail?.name }} 一致</p>

                <label class="mt-5 flex cursor-pointer flex-col items-center justify-center border border-dashed border-line py-7 transition hover:border-ink/30">
                    <input type="file" accept=".zip" class="hidden" @change="onVersionPick" />
                    <span class="text-[12.5px] text-ink-soft">{{ versionFile ? versionFile.name : "选择 zip 文件" }}</span>
                    <span class="mt-1 text-[11px] text-ink-faint">{{ versionFile ? formatSize(versionFile.size) : "拖入或点击选择" }}</span>
                </label>

                <textarea v-model="changelog" rows="3" class="field mt-3 resize-none" placeholder="这次改了什么"></textarea>

                <ul v-if="errors.length" class="mt-3 space-y-1">
                    <li v-for="(item, index) in errors" :key="index" class="text-[11.5px] text-accent">{{ item.field }} · {{ item.message }}</li>
                </ul>

                <div class="mt-5 flex justify-end gap-2">
                    <button class="btn-ghost" @click="showUpload = false">取消</button>
                    <button class="btn-solid" :disabled="!versionFile || uploading" @click="submitVersion">
                        {{ uploading ? "上传中…" : "上传" }}
                    </button>
                </div>
            </div>
        </Modal>

        <!-- 删除确认 -->
        <ConfirmDialog
            :open="showDelete"
            title="删除技能"
            :message="`将永久删除 ${detail?.name} 及其 ${detail?.versions.length ?? 0} 个版本，包文件一并清除，无法恢复。`"
            confirm-label="永久删除"
            tone="danger"
            :busy="deleting"
            @confirm="confirmDelete"
            @cancel="showDelete = false"
        />

        <!-- 版本操作确认 -->
        <ConfirmDialog
            :open="!!pendingAction"
            :title="actionDialog.title"
            :message="actionDialog.message"
            :confirm-label="actionDialog.confirmLabel"
            :tone="actionDialog.tone"
            :busy="actionRunning"
            @confirm="runPendingAction"
            @cancel="pendingAction = null"
        />

        <!-- 转移归属 -->
        <Modal :open="showTransfer" width="max-w-sm" @close="showTransfer = false">
            <div class="border border-line bg-white p-6">
                <h3 class="font-display text-[17px] text-ink">转移归属</h3>
                <p class="mt-2 text-[12.5px] leading-6 text-ink-soft">
                    把 {{ detail?.name }} 的创建者改为其他账号。转移后原创建者失去管理权限。
                </p>
                <select v-model="transferTarget" class="field mt-4">
                    <option value="">选择账号</option>
                    <option v-for="user in transferUsers" :key="user.id" :value="user.username">
                        {{ user.username }}
                    </option>
                </select>
                <div class="mt-5 flex justify-end gap-2">
                    <button class="btn-ghost" @click="showTransfer = false">取消</button>
                    <button class="btn-solid" :disabled="!transferTarget || transferring" @click="submitTransfer">
                        {{ transferring ? "转移中…" : "确认转移" }}
                    </button>
                </div>
            </div>
        </Modal>
        <!-- 全部版本 -->
        <Modal :open="showAllVersions && !!detail" width="max-w-xl" @close="showAllVersions = false">
            <div v-if="detail" class="flex max-h-[78vh] flex-col border border-line bg-paper">
                <div class="flex items-baseline justify-between border-b border-line px-7 py-4">
                    <h3 class="font-display text-[16px] text-ink">所有版本</h3>
                    <span class="font-mono text-[11px] text-ink-faint">{{ detail.versions.length }} 个</span>
                </div>

                <div ref="tabBar" class="relative flex items-center gap-1 border-b border-line px-4 py-2">
                    <span
                        class="pointer-events-none absolute left-0 top-2 h-[30px] bg-ink transition-[transform,width] duration-300 ease-out"
                        :style="sliderStyle"
                    />
                    <button
                        v-for="tab in versionTabs"
                        :key="tab.key"
                        :ref="(el) => setTabRef(tab.key, el as HTMLElement | null)"
                        class="relative z-10 flex h-[30px] items-center gap-1 px-3.5 text-[12px] transition-colors focus:outline-none"
                        :class="versionTab === tab.key ? 'text-white' : 'text-ink-soft hover:text-ink'"
                        @click="switchTab(tab.key)"
                    >
                        {{ tab.label }} <span class="font-mono text-[10.5px] opacity-70">{{ tab.count }}</span>
                    </button>
                </div>

                <div class="mx-4 my-4 h-[380px] overflow-y-auto">
                    <ul v-if="activeTabVersions.length">
                        <li v-for="version in activeTabVersions" :key="version.version">
                            <div
                                class="flex min-h-[76px] flex-col justify-center gap-1 border-b border-line border-l-2 px-4 py-3 transition-colors"
                                :class="[
                                    version.version === detail.current_version ? 'border-l-emerald-600' : version.version === selectedVersion ? 'border-l-ink/40' : 'border-l-transparent',
                                    version.version === selectedVersion ? 'bg-white' : 'hover:bg-white/60',
                                ]"
                            >
                                <button class="block w-full min-w-0 text-left" @click="selectVersion(version.version)">
                                    <span class="flex items-baseline gap-2">
                                        <span class="font-mono text-[12.5px]" :class="version.version === selectedVersion ? 'font-semibold text-ink' : 'text-ink-soft'">v{{ version.version }}</span>
                                        <span class="text-[10px] font-medium tracking-wide uppercase" :class="kindClass(versionKind(version))">{{ kindLabel(versionKind(version)) }}</span>
                                        <span class="ml-auto font-mono text-[10.5px] tabular-nums text-ink-faint">{{ formatDate(version.created_at) }}</span>
                                    </span>
                                    <span class="mt-0.5 block whitespace-normal break-words text-[11.5px] leading-5" :class="version.version === selectedVersion ? 'text-ink-soft' : 'text-ink-faint'">{{ version.changelog || "无变更说明" }}</span>
                                </button>

                                <div class="mt-1 flex items-center justify-between gap-2">
                                    <span class="font-mono text-[10px] text-ink-faint">{{ version.file_count }} 个文件 · {{ formatSize(version.size_bytes) }}</span>
                                    <span v-if="canManage" class="flex items-center gap-1">
                                        <template v-if="versionKind(version) === 'history'">
                                            <button class="border border-ink/25 bg-white px-2.5 py-1 text-[10.5px] text-ink transition hover:bg-ink/[0.04]" @click="requestPublish(version.version)">设为当前</button>
                                            <button class="btn-warn px-2.5 py-1 text-[10.5px]" @click="requestDeprecate(version.version)">废弃</button>
                                        </template>
                                        <button v-else-if="versionKind(version) === 'draft'" class="border border-ink/25 bg-white px-2.5 py-1 text-[10.5px] text-ink transition hover:bg-ink/[0.04]" @click="requestPublish(version.version)">发布</button>
                                        <template v-else-if="versionKind(version) === 'deprecated'">
                                            <button class="btn-quiet px-2.5 py-1 text-[10.5px]" @click="restoreVersionRow(version.version)">恢复</button>
                                            <button v-if="canDelete" class="btn-danger px-2.5 py-1 text-[10.5px]" @click="requestDeleteVersion(version.version)">删除</button>
                                        </template>
                                    </span>
                                </div>
                            </div>
                        </li>
                    </ul>
                    <p v-else class="py-28 text-center text-[12px] text-ink-faint">{{ emptyTabText }}</p>
                </div>

                <div class="flex justify-end border-t border-line px-7 py-3">
                    <button class="btn-quiet" @click="showAllVersions = false">关闭</button>
                </div>
            </div>
        </Modal>
    </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import confetti from "canvas-confetti";

import { listUsers, type User } from "@/@api/auth";
import { ApiError } from "@/@api/http";
import {
    createComment,
    deleteComment,
    deleteSkill,
    deleteVersion,
    deprecateVersion,
    downloadUrl,
    getSkill,
    listComments,
    listFiles,
    publishVersion,
    readFile,
    restoreVersion,
    transferOwner,
    uploadVersion,
    type CommentItem,
    type FileEntry,
    type SkillDetail,
} from "@/@api/skills";
import Modal from "@/components/ui/Modal.vue";
import ConfirmDialog from "@/components/ui/ConfirmDialog.vue";
import FileTree from "@/components/inspira/FileTree.vue";
import { buildTree } from "@/utils/tree";
import { useAuthStore } from "@/store/auth";

defineOptions({ name: "SkillDetailPage" });

interface Block {
    kind: "h1" | "h2" | "h3" | "p" | "li" | "quote" | "code" | "hr";
    text: string;
}

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const name = String(route.params.name);

const detail = ref<SkillDetail | null>(null);
const files = ref<FileEntry[]>([]);
const selectedVersion = ref<number | undefined>(undefined);
const activePath = ref("");
const content = ref("");
const previewLoading = ref(false);
const showUpload = ref(false);
const versionFile = ref<File | null>(null);
const changelog = ref("");
const errors = ref<{ field: string; message: string }[]>([]);
const uploading = ref(false);
const copied = ref(false);
const toast = ref("");
const showAllVersions = ref(false);
const showDelete = ref(false);
const showInstallHelp = ref(false);
const showComments = ref(false);
const comments = ref<CommentItem[]>([]);
const commentTotal = ref(0);
const commentDraft = ref("");
const commentBusy = ref(false);
const commentsLoading = ref(false);
const pendingCommentDelete = ref<string | null>(null);
const COMMENT_PAGE_SIZE = 20;
const deleting = ref(false);
const showTransfer = ref(false);
const transferTarget = ref("");
const transferUsers = ref<User[]>([]);
const transferring = ref(false);
const pendingAction = ref<null | { type: "publish" | "deprecate" | "deleteVersion"; version: number }>(null);
const actionRunning = ref(false);
const versionTab = ref<"main" | "draft" | "deprecated">("main");

// Tab 滑动指示块：不需要引入动画库，直接测量位置后用 CSS 过渡
const tabBar = ref<HTMLElement | null>(null);
const tabRefs = new Map<string, HTMLElement>();
const slider = ref({ left: 0, width: 0, ready: false });

const sliderStyle = computed(() => ({
    transform: `translateX(${slider.value.left}px)`,
    width: `${slider.value.width}px`,
    opacity: slider.value.ready ? 1 : 0,
}));

/**
 * 收集每个 Tab 的 DOM 节点。
 * 调用时机：模板渲染每个 Tab 时由 ref 回调触发。
 */
function setTabRef(key: string, el: HTMLElement | null) {
    if (el) tabRefs.set(key, el);
    else tabRefs.delete(key);
}

/**
 * 重新测量当前选中 Tab 的位置与宽度。
 * 调用时机：切换 Tab、Tab 数量或文案变化、窗口尺寸变化时。
 */
function measureSlider() {
    const el = tabRefs.get(versionTab.value);
    if (!el || el.offsetWidth === 0) return;
    slider.value = { left: el.offsetLeft, width: el.offsetWidth, ready: true };
}


const selectedVersionInfo = computed(() => detail.value?.versions.find((item) => item.version === selectedVersion.value));

/**
 * 判断版本当前的身份：当前 / 历史 / 未发布 / 已废弃。
 * 调用时机：渲染版本行与决定可用操作时。
 */
function versionKind(version: { version: number; status: string }): "current" | "history" | "draft" | "deprecated" {
    if (version.version === detail.value?.current_version) return "current";
    if (version.status === "deprecated") return "deprecated";
    if (version.status === "published") return "history";
    return "draft";
}

const mainVersions = computed(() => (detail.value?.versions ?? []).filter((v) => ["current", "history"].includes(versionKind(v))));
const draftVersions = computed(() => (detail.value?.versions ?? []).filter((v) => versionKind(v) === "draft"));
const deprecatedVersions = computed(() => (detail.value?.versions ?? []).filter((v) => versionKind(v) === "deprecated"));

const versionTabs = computed(() => [
    { key: "main" as const, label: "主线", count: mainVersions.value.length },
    { key: "draft" as const, label: "未发布", count: draftVersions.value.length },
    { key: "deprecated" as const, label: "废弃", count: deprecatedVersions.value.length },
]);

watch([versionTab, versionTabs, showAllVersions], async () => {
    await nextTick();
    measureSlider();
    requestAnimationFrame(measureSlider);
});

onMounted(async () => {
    await nextTick();
    measureSlider();
    window.addEventListener("resize", measureSlider);
});

onBeforeUnmount(() => window.removeEventListener("resize", measureSlider));

const activeTabVersions = computed(() => {
    if (versionTab.value === "draft") return draftVersions.value;
    if (versionTab.value === "deprecated") return deprecatedVersions.value;
    return mainVersions.value;
});

const selectedKind = computed(() => {
    const info = selectedVersionInfo.value;
    return info ? versionKind(info) : null;
});

/**
 * 侧栏展示的版本：当前分组取前 3 个，选中的不在其中时补在末尾。
 * 调用时机：渲染版本列表时。
 */
const visibleVersions = computed(() => {
    const list = mainVersions.value;
    const top = list.slice(0, 3);
    const selected = list.find((item) => item.version === selectedVersion.value);
    if (selected && !top.some((item) => item.version === selected.version)) {
        return [...top, selected];
    }
    return top;
});

const emptyTabText = computed(() => {
    if (versionTab.value === "draft") return "没有未发布的版本";
    if (versionTab.value === "deprecated") return "没有已废弃的版本";
    return "还没有发布过版本";
});

/**
 * 版本操作确认弹窗的文案。
 * 调用时机：渲染确认弹窗时，随待执行操作变化。
 */
const actionDialog = computed(() => {
    const action = pendingAction.value;
    if (!action) return { title: "", message: "", confirmLabel: "确认", tone: "default" as const };
    if (action.type === "publish") {
        const isDraft = selectedVersionInfo.value?.status === "draft";
        return {
            title: isDraft ? "发布版本" : "设为当前版本",
            message: isDraft
                ? `发布 v${action.version} 后，客户端下载会立即切换到该版本。`
                : `将 v${action.version} 设为当前发布版本，客户端下载会立即切换到该版本。`,
            confirmLabel: isDraft ? "发布" : "设为当前",
            tone: "default" as const,
        };
    }
    if (action.type === "deleteVersion") {
        return {
            title: "删除版本",
            message: `将永久删除 v${action.version} 及其包文件，无法恢复。版本号会保留为空号。`,
            confirmLabel: "永久删除",
            tone: "danger" as const,
        };
    }
    return {
        title: "废弃版本",
        message: `废弃 v${action.version} 后，该版本会移出主线，可在「废弃」分组恢复。`,
        confirmLabel: "废弃",
        tone: "warning" as const,
    };
});
let toastTimer: ReturnType<typeof setTimeout> | undefined;

const isSkillMd = computed(() => activePath.value === "SKILL.md");

/** 当前用户能否管理这个技能：管理员，或创建者本人。 */
const canManage = computed(
    () => auth.isLoggedIn && (auth.isAdmin || (Boolean(detail.value?.created_by) && detail.value?.created_by === auth.user?.id)),
);

const canDelete = canManage;

/** 有未发布或废弃版本时，弹窗入口才需要出现。 */
const hasOtherVersions = computed(
    () => detail.value !== null && (detail.value.versions.length > 3 || draftVersions.value.length > 0 || deprecatedVersions.value.length > 0),
);

/** 未发布和历史版本都可以推到当前；游客只读。 */
const canPublish = computed(() => canManage.value && Boolean(selectedKind.value) && ["draft", "history"].includes(selectedKind.value as string));

/** 只有主线里的历史版本可以废弃；游客只读。 */
const canDeprecate = computed(() => canManage.value && selectedKind.value === "history");

const fileTree = computed(() => buildTree(files.value));

const meta = computed(() => {
    if (!isSkillMd.value) return [];
    const match = content.value.match(/^---\n([\s\S]*?)\n---/);
    if (!match) return [];
    return match[1]
        .split("\n")
        .map((line) => {
            const index = line.indexOf(":");
            if (index <= 0) return null;
            return { key: line.slice(0, index).trim(), value: line.slice(index + 1).trim() };
        })
        .filter((entry): entry is { key: string; value: string } => Boolean(entry));
});

const blocks = computed<Block[]>(() => {
    if (!isSkillMd.value) return [];
    let body = content.value.replace(/^---\n[\s\S]*?\n---\n?/, "");
    const result: Block[] = [];
    const lines = body.split("\n");
    let fence: string[] | null = null;

    for (const raw of lines) {
        const line = raw.trimEnd();
        if (line.startsWith("```")) {
            if (fence) {
                result.push({ kind: "code", text: fence.join("\n") });
                fence = null;
            } else {
                fence = [];
            }
            continue;
        }
        if (fence) {
            fence.push(line);
            continue;
        }
        if (!line.trim()) continue;
        if (/^#\s+/.test(line)) result.push({ kind: "h1", text: line.replace(/^#\s+/, "") });
        else if (/^##\s+/.test(line)) result.push({ kind: "h2", text: line.replace(/^##\s+/, "") });
        else if (/^###\s+/.test(line)) result.push({ kind: "h3", text: line.replace(/^###\s+/, "") });
        else if (/^>\s?/.test(line)) result.push({ kind: "quote", text: line.replace(/^>\s?/, "") });
        else if (/^[-*]\s+/.test(line)) result.push({ kind: "li", text: line.replace(/^[-*]\s+/, "") });
        else if (/^\d+\.\s+/.test(line)) result.push({ kind: "li", text: line.replace(/^\d+\.\s+/, "") });
        else if (/^---+$/.test(line)) result.push({ kind: "hr", text: "" });
        else result.push({ kind: "p", text: line });
    }
    if (fence) result.push({ kind: "code", text: fence.join("\n") });

    return result;
});

/**
 * 加载技能详情并选中当前版本。
 * 调用时机：页面挂载时。
 */
async function load(keepVersion?: number) {
    detail.value = await getSkill(name);
    const exists = keepVersion && detail.value.versions.some((item) => item.version === keepVersion);
    selectedVersion.value = exists ? keepVersion : (detail.value.current_version ?? detail.value.versions[0]?.version);

    const info = detail.value.versions.find((item) => item.version === selectedVersion.value);
    const kind = info ? versionKind(info) : null;
    // 默认落在当前版本所在分组；没有当前版本时看未发布
    versionTab.value = kind === "deprecated" ? "deprecated" : kind === "draft" ? "draft" : "main";
    if (selectedVersion.value) await loadFiles(selectedVersion.value);
    void refreshCommentCount();
}

/**
 * 读取评论，重置或追加一页。
 * 调用时机：打开评论弹层、发表成功、删除成功与加载更多时。
 */
async function loadComments(reset: boolean) {
    if (!detail.value) return;
    commentsLoading.value = true;
    try {
        const nextPage = reset ? 1 : Math.floor(comments.value.length / COMMENT_PAGE_SIZE) + 1;
        const result = await listComments(detail.value.name, nextPage, COMMENT_PAGE_SIZE);
        comments.value = reset ? result.items : [...comments.value, ...result.items];
        commentTotal.value = result.total;
    } catch (err) {
        showToast(err instanceof Error ? err.message : "评论加载失败");
    } finally {
        commentsLoading.value = false;
    }
}

/**
 * 打开评论弹层并刷新第一页。
 * 调用时机：点击右下角评论按钮时。
 */
async function openComments() {
    showComments.value = true;
    await loadComments(true);
}

/**
 * 发表评论。
 * 调用时机：评论弹层点击发表按钮时。
 */
async function submitComment() {
    const body = commentDraft.value.trim();
    if (!detail.value || !body) return;
    commentBusy.value = true;
    try {
        await createComment(detail.value.name, body);
        commentDraft.value = "";
        await loadComments(true);
    } catch (err) {
        showToast(err instanceof Error ? err.message : "发表失败");
    } finally {
        commentBusy.value = false;
    }
}

/**
 * 判断评论能否删除：作者本人或管理员。
 * 调用时机：渲染每条评论的删除入口时。
 */
function canRemoveComment(item: CommentItem): boolean {
    return auth.isAdmin || (Boolean(item.author_id) && item.author_id === auth.user?.id);
}

/**
 * 删除评论。
 * 调用时机：确认弹窗点击删除时。
 */
async function confirmDeleteComment() {
    const id = pendingCommentDelete.value;
    if (!detail.value || !id) return;
    commentBusy.value = true;
    try {
        await deleteComment(detail.value.name, id);
        pendingCommentDelete.value = null;
        await loadComments(true);
    } catch (err) {
        showToast(err instanceof Error ? err.message : "删除失败");
    } finally {
        commentBusy.value = false;
    }
}

/**
 * 刷新评论数，用于右下角角标。
 * 调用时机：详情加载完成后。
 */
async function refreshCommentCount() {
    if (!detail.value) return;
    try {
        const result = await listComments(detail.value.name, 1, 1);
        commentTotal.value = result.total;
    } catch {
        // 计数失败不影响正文阅读
    }
}

/**
 * 切换版本分组。
 * 调用时机：点击版本区顶部的 Tab 时。
 */
function switchTab(tab: "main" | "draft" | "deprecated") {
    versionTab.value = tab;
    const list = tab === "draft" ? draftVersions.value : tab === "deprecated" ? deprecatedVersions.value : mainVersions.value;
    if (list.length && !list.some((item) => item.version === selectedVersion.value)) {
        void selectVersion(list[0].version);
    }
}

/**
 * 加载版本文件并默认预览 SKILL.md。
 * 调用时机：首次进入与切换版本时。
 */
async function loadFiles(version: number) {
    files.value = await listFiles(name, version);
    const target = files.value.find((entry) => entry.path === "SKILL.md") ?? files.value[0];
    if (target) await openFile(target.path);
    else {
        activePath.value = "";
        content.value = "";
    }
}

/**
 * 切换版本。
 * 调用时机：点击版本时间线时。
 */
async function selectVersion(version: number) {
    selectedVersion.value = version;
    const info = detail.value?.versions.find((item) => item.version === version);
    if (info) {
        const kind = versionKind(info);
        versionTab.value = kind === "deprecated" ? "deprecated" : kind === "draft" ? "draft" : "main";
    }
    await loadFiles(version);
}


/**
 * 预览文件。
 * 调用时机：点击文件列表项时。
 */
async function openFile(path: string) {
    activePath.value = path;
    previewLoading.value = true;
    try {
        const result = await readFile(name, path, selectedVersion.value);
        content.value = result.content;
    } catch (err) {
        content.value = err instanceof Error ? err.message : "无法预览";
    } finally {
        previewLoading.value = false;
    }
}

/**
 * 请求把选中版本发布或设为当前。
 * 调用时机：未发布版本显示「发布」，历史版本显示「设为当前」，点击后先确认。
 */
function requestPublish(version?: number) {
    const target = version ?? selectedVersion.value;
    if (!target) return;
    pendingAction.value = { type: "publish", version: target };
}

/**
 * 请求废弃选中版本。
 * 调用时机：主线里的历史版本点击「废弃」时。
 */
function requestDeprecate(version?: number) {
    const target = version ?? selectedVersion.value;
    if (!target) return;
    pendingAction.value = { type: "deprecate", version: target };
}

/**
 * 请求删除选中版本。
 * 调用时机：已废弃版本点击「删除」时。
 */
function requestDeleteVersion(version?: number) {
    const target = version ?? selectedVersion.value;
    if (!target) return;
    pendingAction.value = { type: "deleteVersion", version: target };
}

/**
 * 把已废弃版本恢复为历史版本。
 * 调用时机：废弃分组点击「恢复」时，无需二次确认。
 */
async function restoreVersionRow(version: number) {
    try {
        await restoreVersion(name, version);
        versionTab.value = "main";
        if (version === selectedVersion.value) {
            selectedVersion.value = version;
        }
        await load();
    } catch (err) {
        showToast(err instanceof Error ? err.message : "恢复失败");
    }
}

/**
 * 打开全部版本弹窗，并定位到当前选中版本所在分组。
 * 调用时机：点击「查看全部版本」时。
 */
function openAllVersions() {
    const kind = selectedKind.value;
    versionTab.value = kind === "deprecated" ? "deprecated" : kind === "draft" ? "draft" : "main";
    showAllVersions.value = true;
}

/**
 * 执行待确认的操作。
 * 调用时机：确认弹窗点击确认时。
 */
async function runPendingAction() {
    const action = pendingAction.value;
    if (!action) return;
    actionRunning.value = true;
    try {
        if (action.type === "publish") {
            await publishVersion(name, action.version);
            celebrate();
            versionTab.value = "main";
        } else if (action.type === "deprecate") {
            await deprecateVersion(name, action.version);
        } else {
            await deleteVersion(name, action.version);
        }
        pendingAction.value = null;
        const keep = action.type === "deleteVersion" ? undefined : action.version;
        await load(keep);
        if (action.type !== "publish") versionTab.value = "deprecated";
    } catch (err) {
        showToast(err instanceof Error ? err.message : "操作失败");
    } finally {
        actionRunning.value = false;
    }
}

/**
 * 发布后的短暂庆祝效果。
 * 调用时机：版本发布或回滚成功后触发一次，不循环。
 */
function celebrate() {
    confetti({
        particleCount: 90,
        spread: 68,
        startVelocity: 34,
        gravity: 0.9,
        scalar: 0.9,
        ticks: 160,
        origin: { x: 0.5, y: 0.28 },
        colors: ["#c9502c", "#e9b98a", "#121316", "#f2d8ce"],
        disableForReducedMotion: true,
    });
}



/**
 * 打开上传面板。
 * 调用时机：点击顶部「上传新版本」时。
 */
function openUpload() {
    errors.value = [];
    versionFile.value = null;
    changelog.value = "";
    showUpload.value = true;
}

/**
 * 记录选择的包文件。
 * 调用时机：上传面板内选择文件后。
 */
function onVersionPick(event: Event) {
    const target = event.target as HTMLInputElement;
    versionFile.value = target.files?.[0] ?? null;
}

/**
 * 提交新版本。
 * 调用时机：上传面板点击上传时。
 */
async function submitVersion() {
    if (!versionFile.value) return;
    uploading.value = true;
    errors.value = [];
    try {
        await uploadVersion(name, versionFile.value, changelog.value);
        showUpload.value = false;
        await load();
    } catch (err) {
        if (err instanceof ApiError) {
            errors.value = err.details.length ? err.details : [{ field: "package", message: err.message }];
        }
    } finally {
        uploading.value = false;
    }
}

/**
 * 打开转移归属弹窗并加载账号列表。
 * 调用时机：管理员点击顶部「转移」时。
 */
async function openTransfer() {
    showTransfer.value = true;
    transferTarget.value = "";
    try {
        const result = await listUsers();
        transferUsers.value = result.items.filter((item) => item.enabled);
    } catch (err) {
        showToast(err instanceof Error ? err.message : "账号列表加载失败");
    }
}

/**
 * 提交归属转移。
 * 调用时机：转移弹窗点击确认时。
 */
async function submitTransfer() {
    if (!detail.value || !transferTarget.value) return;
    transferring.value = true;
    try {
        await transferOwner(detail.value.name, transferTarget.value);
        showTransfer.value = false;
        showToast("归属已转移");
        await load(selectedVersion.value);
    } catch (err) {
        showToast(err instanceof Error ? err.message : "转移失败");
    } finally {
        transferring.value = false;
    }
}

/**
 * 确认并执行删除。
 * 调用时机：删除确认弹窗点击「永久删除」时；成功后回到列表。
 */
async function confirmDelete() {
    if (!detail.value) return;
    deleting.value = true;
    try {
        await deleteSkill(detail.value.name);
        showDelete.value = false;
        await router.push({ name: "skills" });
    } catch (err) {
        showToast(err instanceof Error ? err.message : "删除失败");
    } finally {
        deleting.value = false;
    }
}

/**
 * 复制当前预览内容，并在页面上给出反馈。
 * 调用时机：点击阅读区右上角「复制」按钮时。
 */
async function copy() {
    try {
        await navigator.clipboard.writeText(content.value);
        copied.value = true;
        showToast("已复制到剪贴板");
        setTimeout(() => {
            copied.value = false;
        }, 1600);
    } catch {
        showToast("复制失败，请手动选择文本");
    }
}

/**
 * 显示一条短暂提示。
 * 调用时机：复制成功或失败、以及其他需要即时反馈的操作后。
 */
function showToast(message: string) {
    toast.value = message;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
        toast.value = "";
    }, 2600);
}

onMounted(load);

/**
 * 版本状态中文名。
 * 调用时机：渲染版本时间线时。
 */
function kindLabel(kind: "current" | "history" | "draft" | "deprecated"): string {
    if (kind === "current") return "当前";
    if (kind === "history") return "历史";
    if (kind === "deprecated") return "已废弃";
    return "未发布";
}

/**
 * 版本身份的文字配色。
 * 调用时机：渲染版本标签时。
 */
function kindClass(kind: "current" | "history" | "draft" | "deprecated"): string {
    if (kind === "current") return "text-emerald-700";
    if (kind === "deprecated") return "text-ink-faint line-through";
    return "text-ink-faint";
}


/**
 * 依据技能名生成稳定渐变色。
 * 调用时机：渲染标题图标时。
 */
function glyph(value: string) {
    let hash = 0;
    for (let i = 0; i < value.length; i += 1) hash = (hash * 31 + value.charCodeAt(i)) % 360;
    return { background: `linear-gradient(140deg, hsl(${hash} 42% 46%), hsl(${(hash + 38) % 360} 46% 34%))` };
}

/**
 * 格式化体积。
 * 调用时机：渲染文件与版本信息时。
 */
function formatSize(bytes: number): string {
    if (!bytes) return "—";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

/**
 * 格式化日期。
 * 调用时机：渲染时间线时。
 */
function formatDate(value: string): string {
    return new Date(value).toLocaleDateString("zh-CN", { month: "2-digit", day: "2-digit" });
}
</script>
<style scoped>
.toast-enter-active,
.toast-leave-active {
    transition: opacity 0.2s ease, transform 0.2s ease;
}

.toast-enter-from,
.toast-leave-to {
    opacity: 0;
    transform: translate(-50%, 8px);
}
</style>