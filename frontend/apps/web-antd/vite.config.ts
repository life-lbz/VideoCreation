import { defineConfig } from '@vben/vite-config';

export default defineConfig(async () => {
  return {
    application: {},
    vite: {
      server: {
        proxy: {
          '/api': {
            changeOrigin: true,
            // mock代理目标地址
            target: 'http://127.0.0.1:4173',
            ws: true,
          },
        },
      },
    },
  };
});
