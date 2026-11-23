/** 文件树构建。调用时机：详情页把扁平文件列表转成可折叠目录结构时。 */

import type { FileEntry } from "@/@api/skills";

export interface TreeNode {
    name: string;
    path: string;
    size: number;
    children: TreeNode[];
}

/**
 * 把扁平路径列表组装为目录树。
 * 调用时机：每次文件列表加载完成后调用一次。
 */
export function buildTree(entries: FileEntry[]): TreeNode[] {
    const root: TreeNode[] = [];
    for (const entry of entries) {
        const parts = entry.path.split("/");
        let level = root;
        parts.forEach((part, index) => {
            const isFile = index === parts.length - 1;
            const path = parts.slice(0, index + 1).join("/");
            let node = level.find((item) => item.name === part);
            if (!node) {
                node = { name: part, path, size: isFile ? entry.size : 0, children: [] };
                level.push(node);
            }
            level = node.children;
        });
    }
    return root;
}
