/// <reference types="vite/client" />

interface ImportMetaEnv {
    /** 后端 API 地址; 留空则使用同源(生产默认)。 */
    readonly VITE_API_BASE_URL?: string
}

interface ImportMeta {
    readonly env: ImportMetaEnv
}
