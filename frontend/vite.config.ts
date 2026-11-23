import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";
import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";

// 开发时把接口与索引请求代理到本地后端，生产由 Nginx 同源反代
export default defineConfig({
    plugins: [vue(), tailwindcss()],
    resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
    server: {
        host: "0.0.0.0",
        port: 18139,
        strictPort: true,
        proxy: {
            "/api": { target: "http://127.0.0.1:18138", changeOrigin: true },
            "/.well-known": { target: "http://127.0.0.1:18138", changeOrigin: true },
        },
    },
    build: { outDir: "dist", sourcemap: false },
});
