import { defineConfig } from '@vben/vite-config';

export default defineConfig(async () => {
  const apiTarget = process.env.VITE_API_PROXY_TARGET ?? 'http://127.0.0.1:4173';
  return {
    application: {},
    vite: {
      server: {
        proxy: {
          '/api': {
            changeOrigin: true,
            target: apiTarget,
            ws: true,
          },
        },
      },
    },
  };
});
