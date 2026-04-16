import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const apiProxyTarget = env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8000';
  const devPort = Number(env.VITE_PORT || 5173);

  return {
    plugins: [react()],
    server: {
      host: '0.0.0.0',
      port: devPort,
      strictPort: true,
      proxy: {
        '/api/v2': {
          target: apiProxyTarget,
          changeOrigin: true,
          secure: false,
        },
      },
    },
  };
});
