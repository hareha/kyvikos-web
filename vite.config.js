import { defineConfig } from 'vite';

export default defineConfig({
  // 상대 경로로 빌드해서 어떤 호스팅 경로에 올려도 동작하게 합니다.
  base: './',
  server: { port: 5173, strictPort: true },
  // 배포마다 바뀌는 값: 이름이 고정된 3D 파일(glb·라이트맵·그래픽)의 브라우저 캐시를 끊는다
  define: { __BUILD__: JSON.stringify(Date.now().toString(36)) },
});
