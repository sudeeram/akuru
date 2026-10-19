'use client';

import { useEffect, useId, useState, type ReactNode } from 'react';
import {
  BookOpen,
  ChevronRight,
  Menu,
  PanelLeftClose,
  PanelLeftOpen,
  Search,
  Settings2,
  type LucideIcon,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';

export type PortalNavItem = {
  id: string;
  label: string;
  icon: LucideIcon;
  group: string;
  badge?: number;
  href?: string;
};

export function PortalShell({
  items,
  active,
  onNavigate,
  title,
  context,
  account,
  actions,
  children,
  footer,
  preview = false,
  breadcrumbs,
  onNavigatePath,
  workspaceContext,
  focusAvailable = false,
}: {
  items: PortalNavItem[];
  active: string;
  onNavigate: (id: string) => void;
  title: string;
  context: string;
  account: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  preview?: boolean;
  breadcrumbs?: { label: string; path?: string }[];
  onNavigatePath?: (path: string) => void;
  workspaceContext?: ReactNode;
  focusAvailable?: boolean;
}) {
  const [focused, setFocused] = useState(false);
  useEffect(() => {
    const change = (event: Event) =>
      setFocused(Boolean((event as CustomEvent<boolean>).detail));
    window.addEventListener('akuru:learning-focus', change);
    return () => window.removeEventListener('akuru:learning-focus', change);
  }, []);
  useEffect(() => {
    if (!focusAvailable) setFocused(false);
  }, [focusAvailable]);
  const searchId = useId();
  const [density, setDensity] = useState<'compact' | 'comfortable'>('compact');
  useEffect(() => {
    try {
      const saved = localStorage.getItem('akuru-ui-density');
      if (saved === 'compact' || saved === 'comfortable') setDensity(saved);
    } catch {
      /* Private browsing may disable preference storage. */
    }
  }, []);
  const toggleDensity = () => {
    const next = density === 'compact' ? 'comfortable' : 'compact';
    setDensity(next);
    try {
      localStorage.setItem('akuru-ui-density', next);
    } catch {
      /* Keep the in-memory preference. */
    }
  };
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [search, setSearch] = useState('');
  const filtered = items.filter((item) =>
    item.label.toLowerCase().includes(search.toLowerCase().trim()),
  );
  const navigation = (compact = false, mobile = false) => (
    <>
      {!compact && (
        <label
          className="ak-nav-search"
          htmlFor={`${searchId}-${mobile ? 'mobile' : 'desktop'}`}
        >
          <Search size={16} />
          <span className="sr-only">Search navigation</span>
          <Input
            id={`${searchId}-${mobile ? 'mobile' : 'desktop'}`}
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Find a page…"
          />
        </label>
      )}
      <nav
        aria-label={preview ? 'UI feature categories' : `${context} sections`}
        className="ak-navigation"
      >
        {[...new Set(filtered.map((item) => item.group))].map((group) => (
          <div className="ak-nav-group" key={group}>
            {!compact && <p>{group}</p>}
            {filtered
              .filter((item) => item.group === group)
              .map(({ id, label, icon: Icon, badge, href }) => {
                const content = (
                  <>
                    <Icon size={18} />
                    <span className={compact ? 'sr-only' : ''}>{label}</span>
                    {!!badge && !compact && <small>{badge}</small>}
                  </>
                );
                return href ? (
                  <a
                    key={id}
                    href={href}
                    title={compact ? label : undefined}
                    onClick={() => setMobileOpen(false)}
                  >
                    {content}
                  </a>
                ) : (
                  <button
                    key={id}
                    type="button"
                    aria-current={active === id ? 'page' : undefined}
                    title={compact ? label : undefined}
                    onClick={() => {
                      onNavigate(id);
                      setMobileOpen(false);
                    }}
                  >
                    {content}
                  </button>
                );
              })}
          </div>
        ))}
        {!filtered.length && <p className="ak-nav-empty">No matching pages.</p>}
      </nav>
    </>
  );
  return (
    <div
      className="ak-shell"
      data-collapsed={collapsed}
      data-density={density}
      data-focus={focused && focusAvailable}
    >
      <a className="skip-link" href="#main-content">
        Skip to page content
      </a>
      <aside className="ak-sidebar">
        <div className="ak-brand">
          <span className="ak-brand-mark">
            <BookOpen size={23} />
          </span>
          {!collapsed && (
            <span>
              AKURU<small>A little progress, every day.</small>
            </span>
          )}
        </div>
        {!collapsed && (
          <div className="ak-workspace">
            <span className="ak-workspace-icon">
              <BookOpen size={20} />
            </span>
            <div>
              <strong>{context}</strong>
              <small>
                {preview
                  ? 'Design preview · sample data'
                  : 'Your learning workspace'}
              </small>
            </div>
          </div>
        )}
        {navigation(collapsed)}
        <div className="ak-sidebar-bottom">
          <Button
            variant="ghost"
            size={collapsed ? 'icon' : 'default'}
            onClick={() => {
              setCollapsed(!collapsed);
              setSearch('');
            }}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? (
              <PanelLeftOpen />
            ) : (
              <>
                <PanelLeftClose /> Collapse sidebar
              </>
            )}
          </Button>
        </div>
      </aside>
      <div className="ak-shell-body">
        <header className="ak-topbar">
          <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
            <SheetTrigger
              render={
                <Button
                  variant="outline"
                  size="icon"
                  className="ak-mobile-menu"
                  aria-label="Open navigation"
                />
              }
            >
              <Menu />
            </SheetTrigger>
            <SheetContent side="left" className="ak-mobile-sheet">
              <SheetHeader>
                <SheetTitle>AKURU · {context}</SheetTitle>
                <SheetDescription>Choose a section</SheetDescription>
              </SheetHeader>
              {navigation(false, true)}
            </SheetContent>
          </Sheet>
          <nav className="ak-breadcrumb" aria-label="Breadcrumb">
            <span>{context}</span>
            <ChevronRight size={14} />
            {breadcrumbs?.length ? (
              <ol>
                {breadcrumbs.map((crumb, index) => (
                  <li key={`${crumb.label}-${index}`}>
                    {crumb.path && onNavigatePath ? (
                      <button
                        type="button"
                        onClick={() => onNavigatePath(crumb.path!)}
                      >
                        {crumb.label}
                      </button>
                    ) : (
                      <strong
                        aria-current={
                          index === breadcrumbs.length - 1 ? 'page' : undefined
                        }
                      >
                        {crumb.label}
                      </strong>
                    )}
                    {index < breadcrumbs.length - 1 && (
                      <ChevronRight size={12} />
                    )}
                  </li>
                ))}
              </ol>
            ) : (
              <strong>{title}</strong>
            )}
          </nav>
          <div className="ak-header-actions">
            {focusAvailable && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => setFocused(!focused)}
                aria-pressed={focused}
              >
                {focused ? 'Exit focus' : 'Focus view'}
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              className="ak-density-toggle"
              onClick={toggleDensity}
              aria-label="Compact view"
              aria-pressed={density === 'compact'}
              title={
                density === 'compact'
                  ? 'Switch to comfortable spacing'
                  : 'Switch to compact spacing'
              }
            >
              <Settings2 size={16} />
              <span>{density === 'compact' ? 'Compact' : 'Comfortable'}</span>
            </Button>
            {actions}
            {account}
          </div>
        </header>
        <main id="main-content" tabIndex={-1} className="ak-main">
          {workspaceContext}
          {children}
        </main>
        <footer className="ak-footer">
          {footer ?? (
            <>
              <span>AKURU · A little progress, every day.</span>
              <span>iGCSE learning workspace</span>
            </>
          )}
        </footer>
      </div>
    </div>
  );
}
