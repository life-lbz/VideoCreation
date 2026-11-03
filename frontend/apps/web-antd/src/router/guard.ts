import type { Router } from 'vue-router';
import { useAccessStore } from '@vben/stores';
import { generateAccess } from './access';
import { accessRoutes } from './routes';
export function createRouterGuard(router: Router) {
  router.beforeEach(async () => {
    const store = useAccessStore();
    if (!store.isAccessChecked) {
      const { accessibleMenus, accessibleRoutes } = await generateAccess({
        roles: [],
        router,
        routes: accessRoutes,
      });
      store.setAccessMenus(accessibleMenus);
      store.setAccessRoutes(accessibleRoutes);
      store.setIsAccessChecked(true);
    }
    return true;
  });
}
