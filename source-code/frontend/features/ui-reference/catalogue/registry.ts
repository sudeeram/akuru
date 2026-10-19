export const catalogueEntries = [
  {
    id: 'alerts',
    title: 'Alerts',
    group: 'Identity & feedback',
    description:
      'Labelled information, success, warning and error notices with local dismissal and retry.',
    primitive: 'alert',
  },
  {
    id: 'accordion',
    title: 'Accordion',
    group: 'Disclosure & overlays',
    description:
      'Bordered, flush, multiple-open and arrowless disclosure patterns.',
    primitive: 'accordion',
  },
  {
    id: 'avatar',
    title: 'Avatar',
    group: 'Identity & feedback',
    description:
      'Original AKURU characters, initials, sizes, groups and sample identity tiles.',
    primitive: 'avatar',
  },
  {
    id: 'badges',
    title: 'Badges',
    group: 'Identity & feedback',
    description:
      'Semantic status, metadata and counts, with decorative dark and RTL specimens.',
    primitive: '../portal/badges',
  },
  {
    id: 'buttons',
    title: 'Buttons',
    group: 'Actions & navigation',
    description:
      'Primary, secondary, compact, icon, toggle, pending and decorative action controls.',
    primitive: 'button',
  },
  {
    id: 'buttons-group',
    title: 'Button groups',
    group: 'Actions & navigation',
    description:
      'Related actions, period choices, multiple selection and vertical controls.',
    primitive: 'button-group',
  },
  {
    id: 'breadcrumb',
    title: 'Breadcrumb',
    group: 'Actions & navigation',
    description: 'Compact hierarchy trails with alternate separators.',
    primitive: 'breadcrumb',
  },
  {
    id: 'cards',
    title: 'Cards',
    group: 'Foundations & layout',
    description:
      'Divided headers, bodies and footers for course, profile, review and media cards.',
    primitive: 'card',
  },
  {
    id: 'carousel',
    title: 'Carousel',
    group: 'Disclosure & overlays',
    description:
      'Manual resource slides with controls, indicators, captions and opt-in timing.',
    primitive: 'carousel',
  },
  {
    id: 'collapse',
    title: 'Collapse',
    group: 'Disclosure & overlays',
    description:
      'Independent guidance panels and a shared toggle for multiple regions.',
    primitive: 'collapsible',
  },
  {
    id: 'dropdowns',
    title: 'Dropdowns',
    group: 'Disclosure & overlays',
    description:
      'Action menus, checked choices, disabled items, split actions and four placements.',
    primitive: 'dropdown-menu',
  },
  {
    id: 'grid',
    title: 'Grid',
    group: 'Foundations & layout',
    description:
      'Responsive equal, unequal and nested layouts with width previews.',
    primitive: 'CSS grid',
  },
  {
    id: 'images',
    title: 'Images',
    group: 'Foundations & layout',
    description:
      'Original artwork with shape, alignment, caption and fallback patterns.',
    primitive: 'aspect-ratio',
  },
  {
    id: 'links',
    title: 'Links',
    group: 'Actions & navigation',
    description:
      'Readable inline and secondary links with visible focus and underline treatments.',
    primitive: 'next/link',
  },
  {
    id: 'list-group',
    title: 'List group',
    group: 'Actions & navigation',
    description:
      'Resource rows, numbered steps, counts and locally actionable lists.',
    primitive: 'item',
  },
  {
    id: 'modals',
    title: 'Modals',
    group: 'Disclosure & overlays',
    description:
      'A validated sample editor, two-step confirmation, sizes and scrollable guidance.',
    primitive: 'dialog',
  },
  {
    id: 'offcanvas',
    title: 'Offcanvas',
    group: 'Disclosure & overlays',
    description: 'Contextual resource drawers in four placements.',
    primitive: 'sheet',
  },
  {
    id: 'pagination',
    title: 'Pagination',
    group: 'Actions & navigation',
    description: 'Controlled resource pages with current and disabled states.',
    primitive: 'pagination',
  },
  {
    id: 'popovers',
    title: 'Popovers',
    group: 'Disclosure & overlays',
    description: 'Contextual explanations and small local filter forms.',
    primitive: 'popover',
  },
  {
    id: 'progress',
    title: 'Progress',
    group: 'Identity & feedback',
    description:
      'Labelled completion, segmented meters, gauges and sample activity trends.',
    primitive: 'progress',
  },
  {
    id: 'placeholders',
    title: 'Placeholders',
    group: 'Identity & feedback',
    description: 'Matched loading/content cards and reusable skeleton shapes.',
    primitive: 'skeleton',
  },
  {
    id: 'workspace',
    title: 'Workspace',
    group: 'Composed patterns',
    description:
      'Search, filters, selection, density, cards, details and pagination over sample documents.',
    primitive: '../portal/workspace',
  },
  {
    id: 'attendance',
    title: 'Attendance',
    group: 'Composed patterns',
    description:
      'A fictional register, daily heatmap, sessions and comparison summaries.',
    primitive: './activity-patterns',
  },
  {
    id: 'spinner',
    title: 'Spinner',
    group: 'Identity & feedback',
    description: 'Inline indicators and bounded, repeat-safe loading actions.',
    primitive: 'spinner',
  },
  {
    id: 'nav-tabs',
    title: 'Nav & tabs',
    group: 'Actions & navigation',
    description:
      'Line, segmented, counted and vertical panels with disabled choices.',
    primitive: 'tabs',
  },
  {
    id: 'tooltips',
    title: 'Tooltips',
    group: 'Disclosure & overlays',
    description:
      'Concise keyboard-accessible help with placement and disabled-action guidance.',
    primitive: 'tooltip',
  },
  {
    id: 'typography',
    title: 'Typography',
    group: 'Foundations & layout',
    description:
      'Panel hierarchy, body text, semantic emphasis, lists and definitions.',
    primitive: 'Semantic HTML',
  },
] as const;
export type CatalogueId = (typeof catalogueEntries)[number]['id'];
export function findEntries(query: string) {
  const words = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
  return catalogueEntries.filter((entry) =>
    words.every((word) =>
      `${entry.title} ${entry.group} ${entry.description}`
        .toLowerCase()
        .includes(word),
    ),
  );
}
export function catalogueFromHash(hash: string): CatalogueId | null {
  const id = hash.replace(/^#ui-catalog-/, '');
  return hash.startsWith('#ui-catalog-') &&
    catalogueEntries.some((entry) => entry.id === id)
    ? (id as CatalogueId)
    : null;
}
