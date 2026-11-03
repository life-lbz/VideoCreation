import type { RouteRecordRaw } from 'vue-router';
const routes: RouteRecordRaw[] = [
  {
    name: 'FrameFlowVideoProviders',
    path: '/settings/video-providers',
    component: () => import('#/views/frameflow/providers/index.vue'),
    meta: { title: '视频接口配置', icon: 'lucide:wallet-cards', order: 7 },
  },
  {
    name: 'FrameFlowdashboard',
    path: '/dashboard',
    component: () => import('#/views/frameflow/dashboard/index.vue'),
    meta: { title: '工作台', icon: 'lucide:layout-dashboard', order: 1 },
  },
  {
    name: 'FrameFlowstudio',
    path: '/studio',
    component: () => import('#/views/frameflow/studio/index.vue'),
    meta: { title: '视频创作', icon: 'lucide:clapperboard', order: 2 },
  },
  {
    name: 'FrameFlowworks',
    path: '/works',
    component: () => import('#/views/frameflow/works/index.vue'),
    meta: { title: '我的作品', icon: 'lucide:library', order: 3 },
  },
  {
    name: 'FrameFlowtemplates',
    path: '/templates',
    component: () => import('#/views/frameflow/templates/index.vue'),
    meta: { title: '灵感模板', icon: 'lucide:sparkles', order: 4 },
  },
  {
    name: 'FrameFlowassets',
    path: '/assets',
    component: () => import('#/views/frameflow/assets/index.vue'),
    meta: { title: '品牌素材', icon: 'lucide:images', order: 5 },
  },
  {
    name: 'FrameFlowbilling',
    path: '/billing',
    component: () => import('#/views/frameflow/billing/index.vue'),
    meta: { title: '套餐与账单', icon: 'lucide:wallet-cards', order: 6 },
  },
];
export default routes;
