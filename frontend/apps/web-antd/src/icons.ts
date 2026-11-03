import { addIcon } from '@vben/icons';
// Keep shell icons local so the application works with script/connect-src 'self'.
const paths: Record<string, string> = {
  'lucide:layout-dashboard':
    '<rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/>',
  'lucide:clapperboard':
    '<rect x="3" y="7" width="18" height="14" rx="2"/><path d="M3 7V3h18v4M7 3l3 4m5-4 3 4"/>',
  'lucide:library': '<path d="M4 3v18M9 3v18m5-18v18m3-17 4 16"/>',
  'lucide:sparkles': '<path d="m12 3 3 6 6 3-6 3-3 6-3-6-6-3 6-3Z"/>',
  'lucide:images':
    '<rect x="6" y="3" width="15" height="15" rx="2"/><path d="M3 7v12a2 2 0 0 0 2 2h12M6 15l5-5 4 4 3-3 3 3"/><circle cx="16" cy="7" r="1"/>',
  'lucide:wallet-cards':
    '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18m-6 5h6"/>',
  'ep:fold': '<path d="M4 5h16M4 19h16M11 9h9m-9 6h9M7 9l-3 3 3 3"/>',
  'fluent-mdl2:world-clock':
    '<circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 2"/>',
  'mdi:keyboard-esc':
    '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M7 9H5v6h2m-2-3h2m4-3H9v3h2v3H9m7-6h-2v6h2"/>',
};
for (const [name, path] of Object.entries(paths))
  addIcon(name, {
    width: 24,
    height: 24,
    body:
      '<g fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">' +
      path +
      '</g>',
  });
