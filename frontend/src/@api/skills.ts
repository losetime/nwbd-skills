/** 技能接口。调用时机：列表、详情、上传、发布与下载相关页面。 */

import { request } from "./http";

export interface SkillSummary {
    name: string;
    display_name: string;
    summary: string;
    status: "active" | "archived";
    version_count: number;
    current_version: number | null;
    file_count: number;
    size_bytes: number;
    updated_at: string;
}

export interface Version {
    version: number;
    status: "draft" | "published" | "deprecated";
    changelog: string;
    size_bytes: number;
    file_count: number;
    package_sha256: string;
    created_at: string;
    published_at: string | null;
    validation: { errors?: unknown[]; warnings?: { field: string; message: string }[] };
}

export interface SkillDetail {
    name: string;
    display_name: string;
    summary: string;
    status: string;
    current_version: number | null;
    created_by: string | null;
    created_at: string;
    updated_at: string;
    versions: Version[];
}

export interface FileEntry {
    path: string;
    size: number;
}

export interface UploadResult {
    name: string;
    version: number;
    status: string;
    warnings: { field: string; message: string }[];
    duplicate_of: number | null;
}

export interface Stats {
    skill_count: number;
    version_count: number;
    published_count: number;
    recent: { action: string; actor: string; skill: string; version: number | null; at: string }[];
}

/**
 * 分页查询技能。
 * 调用时机：列表页加载、搜索与翻页时。
 */
export function listSkills(params: { q?: string; status?: string; page?: number; size?: number }): Promise<{
    items: SkillSummary[];
    total: number;
    page: number;
    size: number;
}> {
    const query = new URLSearchParams();
    if (params.q) query.set("q", params.q);
    if (params.status) query.set("status", params.status);
    query.set("page", String(params.page ?? 1));
    query.set("size", String(params.size ?? 20));
    return request(`/api/skills?${query.toString()}`);
}

/**
 * 读取技能详情与版本列表。
 * 调用时机：进入详情页时。
 */
export function getSkill(name: string): Promise<SkillDetail> {
    return request<SkillDetail>(`/api/skills/${encodeURIComponent(name)}`);
}

/**
 * 列出指定版本包内文件。
 * 调用时机：详情页切换版本或首次加载时。
 */
export function listFiles(name: string, version?: number): Promise<FileEntry[]> {
    const suffix = version ? `?version=${version}` : "";
    return request<FileEntry[]>(`/api/skills/${encodeURIComponent(name)}/files${suffix}`);
}

/**
 * 读取单个文件内容用于预览。
 * 调用时机：文件树点击某个文件时。
 */
export function readFile(name: string, path: string, version?: number): Promise<{ path: string; content: string }> {
    const query = new URLSearchParams({ path });
    if (version) query.set("version", String(version));
    return request(`/api/skills/${encodeURIComponent(name)}/file?${query.toString()}`);
}

/**
 * 上传全新技能。
 * 调用时机：上传页选择 zip 并提交时。
 */
export function uploadSkill(file: File, changelog: string): Promise<UploadResult> {
    const form = new FormData();
    form.append("file", file);
    form.append("changelog", changelog);
    return request<UploadResult>("/api/skills", { method: "POST", body: form });
}

/**
 * 为既有技能上传新版本。
 * 调用时机：详情页点击上传新版本时。
 */
export function uploadVersion(name: string, file: File, changelog: string): Promise<UploadResult> {
    const form = new FormData();
    form.append("file", file);
    form.append("changelog", changelog);
    return request<UploadResult>(`/api/skills/${encodeURIComponent(name)}/versions`, { method: "POST", body: form });
}

/**
 * 发布指定版本。
 * 调用时机：详情页点击发布时。
 */
export function publishVersion(name: string, version: number): Promise<Version> {
    return request<Version>(`/api/skills/${encodeURIComponent(name)}/versions/${version}/publish`, { method: "POST" });
}


/**
 * 废弃指定版本。
 * 调用时机：详情页对版本点击废弃时。
 */
export function deprecateVersion(name: string, version: number): Promise<{ version: number; status: string }> {
    return request(`/api/skills/${encodeURIComponent(name)}/versions/${version}/deprecate`, { method: "POST" });
}

/**
 * 把已废弃版本恢复为历史版本。
 * 调用时机：在废弃分组点击恢复时。
 */
export function restoreVersion(name: string, version: number): Promise<{ version: number; status: string }> {
    return request(`/api/skills/${encodeURIComponent(name)}/versions/${version}/restore`, { method: "POST" });
}

/**
 * 物理删除单个已废弃版本。
 * 调用时机：创建者在废弃分组点击删除并确认后。
 */
export function deleteVersion(name: string, version: number): Promise<{ version: number; deleted: boolean }> {
    return request(`/api/skills/${encodeURIComponent(name)}/versions/${version}`, { method: "DELETE" });
}

/**
 * 彻底删除技能。
 * 调用时机：创建者在详情页确认删除时。
 */
export function deleteSkill(name: string): Promise<{ name: string; deleted: boolean }> {
    return request(`/api/skills/${encodeURIComponent(name)}`, { method: "DELETE" });
}

export interface CommentItem {
    id: string;
    author: string;
    author_id: string | null;
    body: string;
    created_at: string;
}

/**
 * 读取技能评论。
 * 调用时机：详情页打开评论弹层与加载更多时。
 */
export function listComments(name: string, page = 1, size = 20): Promise<{ items: CommentItem[]; total: number }> {
    return request(`/api/skills/${encodeURIComponent(name)}/comments?page=${page}&size=${size}`);
}

/**
 * 发表评论。
 * 调用时机：登录用户在评论弹层点击发表时。
 */
export function createComment(name: string, body: string): Promise<CommentItem> {
    return request(`/api/skills/${encodeURIComponent(name)}/comments`, {
        method: "POST",
        body: JSON.stringify({ body }),
    });
}

/**
 * 删除评论。
 * 调用时机：作者本人或管理员在评论列表点击删除并确认后。
 */
export function deleteComment(name: string, id: string): Promise<{ deleted: boolean }> {
    return request(`/api/skills/${encodeURIComponent(name)}/comments/${id}`, { method: "DELETE" });
}

/**
 * 拼接下载地址。
 * 调用时机：详情页点击下载时。
 */
export function downloadUrl(name: string, version?: number): string {
    const suffix = version ? `?version=${version}` : "";
    return `/api/skills/${encodeURIComponent(name)}/download${suffix}`;
}

/**
 * 读取概览统计。
 * 调用时机：概览页加载时。
 */
export function getStats(): Promise<Stats> {
    return request<Stats>("/api/stats");
}

export interface AuditItem {
    id: string;
    action: string;
    actor: string;
    skill: string;
    version: number | null;
    detail: Record<string, unknown>;
    at: string;
}

/**
 * 查询审计记录。
 * 调用时机：审计页加载与筛选时。
 */
export function listAudit(params: { action?: string; page?: number; size?: number }): Promise<{
    items: AuditItem[];
    total: number;
}> {
    const query = new URLSearchParams();
    if (params.action) query.set("action", params.action);
    query.set("page", String(params.page ?? 1));
    query.set("size", String(params.size ?? 30));
    return request(`/api/audit?${query.toString()}`);
}

/**
 * 转移技能归属。
 * 调用时机：管理员在详情页确认转移归属时。
 */
export function transferOwner(name: string, username: string): Promise<{ name: string; created_by: string }> {
    return request(`/api/skills/${encodeURIComponent(name)}/owner`, {
        method: "PATCH",
        body: JSON.stringify({ username }),
    });
}
