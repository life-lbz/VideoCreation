import type { RouteRecordRaw } from 'vue-router';
import frameflow from './modules/frameflow';
const routes: RouteRecordRaw[] = [
  {
    name: 'Root',
    path: '/',
    component: () => import('#/layouts/basic.vue'),
    redirect: '/dashboard',
    meta: { title: 'FrameFlow' },
    children: frameflow,
  },
  { path: '/:path(.*)*', redirect: '/dashboard' },
];
const accessRoutes = frameflow;
const coreRouteNames = ['Root'];
export { routes, accessRoutes, coreRouteNames };
