import { defineConfig } from 'vite';

export default defineConfig({
  // 상대 경로로 빌드해서 어떤 호스팅 경로에 올려도 동작하게 합니다.
  base: './',
  server: { port: 5173, strictPort: true },
});
