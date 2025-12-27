// frontend/src/vite-env.d.ts
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_WS_URL: string
  readonly VITE_APP_NAME: string
  // Add more env variables as needed
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}