import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Bot,
  Database,
  FlaskConical,
  BrainCircuit,
  Settings,
  ChevronLeft,
  ChevronRight,
  Sparkles,
} from 'lucide-react'
import { useSidebar } from '@/hooks/useSidebar'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/utils/cn'

// ─── Nav Items ────────────────────────────────────────────────────

const NAV_ITEMS = [
  {
    label: 'Dashboard',
    href: '/',
    icon: LayoutDashboard,
    end: true,
  },
  {
    label: 'Agents',
    href: '/agents',
    icon: Bot,
    end: false,
  },
  {
    label: 'Datasets',
    href: '/datasets',
    icon: Database,
    end: false,
  },
  {
    label: 'Experiments',
    href: '/experiments',
    icon: FlaskConical,
    end: false,
  },
  {
    label: 'Models',
    href: '/models',
    icon: BrainCircuit,
    end: false,
  },
] as const

const BOTTOM_ITEMS = [
  {
    label: 'Settings',
    href: '/settings',
    icon: Settings,
    end: false,
  },
] as const

// ─── Sidebar Component ────────────────────────────────────────────

export function Sidebar() {
  const { isCollapsed, toggle } = useSidebar()

  return (
    <aside
      className={cn(
        'relative hidden md:flex flex-col h-screen border-r border-sidebar-border bg-sidebar text-sidebar-foreground transition-all duration-300 ease-in-out',
        isCollapsed ? 'w-[68px]' : 'w-[240px]'
      )}
    >
      {/* ── Logo ── */}
      <div
        className={cn(
          'flex h-16 items-center border-b border-sidebar-border px-4 shrink-0',
          isCollapsed ? 'justify-center' : 'justify-between'
        )}
      >
        {!isCollapsed && (
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg gradient-primary shadow-lg shadow-blue-500/20">
              <Sparkles className="h-4 w-4 text-white" />
            </div>
            <div>
              <p className="text-sm font-bold text-white leading-none">AutoDS</p>
              <p className="text-[10px] text-sidebar-foreground/50 leading-none mt-0.5">
                Autonomous Data Scientist
              </p>
            </div>
          </div>
        )}

        {isCollapsed && (
          <div className="flex h-8 w-8 items-center justify-center rounded-lg gradient-primary shadow-lg shadow-blue-500/20">
            <Sparkles className="h-4 w-4 text-white" />
          </div>
        )}
      </div>

      {/* ── Navigation ── */}
      <ScrollArea className="flex-1 py-4">
        <nav className="space-y-1 px-2">
          {NAV_ITEMS.map(({ label, href, icon: Icon, end }) => (
            <NavLink
              key={href}
              to={href}
              end={end}
              className={({ isActive }) =>
                cn(
                  'group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200',
                  isActive
                    ? 'bg-sidebar-accent text-white shadow-sm'
                    : 'text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground',
                  isCollapsed && 'justify-center px-2'
                )
              }
            >
              {({ isActive }) => (
                <>
                  {/* Active left border indicator */}
                  {isActive && !isCollapsed && (
                    <span className="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-0.5 rounded-full bg-blue-400" />
                  )}

                  <Icon
                    className={cn(
                      'h-4 w-4 shrink-0 transition-transform duration-200',
                      !isCollapsed && 'group-hover:scale-110'
                    )}
                  />

                  {!isCollapsed && (
                    <span className="truncate">{label}</span>
                  )}

                  {/* Tooltip when collapsed */}
                  {isCollapsed && (
                    <div className="absolute left-full ml-2 z-50 hidden group-hover:flex items-center">
                      <div className="rounded-md bg-popover border border-border px-2.5 py-1.5 text-xs font-medium text-popover-foreground shadow-md whitespace-nowrap">
                        {label}
                      </div>
                    </div>
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {!isCollapsed && (
          <>
            <Separator className="my-4 mx-2 bg-sidebar-border" />
            <div className="px-3 mb-2">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-sidebar-foreground/40">
                System
              </p>
            </div>
          </>
        )}
        {isCollapsed && <Separator className="my-4 mx-2 bg-sidebar-border" />}

        <nav className="space-y-1 px-2">
          {BOTTOM_ITEMS.map(({ label, href, icon: Icon, end }) => (
            <NavLink
              key={href}
              to={href}
              end={end}
              className={({ isActive }) =>
                cn(
                  'group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200',
                  isActive
                    ? 'bg-sidebar-accent text-white shadow-sm'
                    : 'text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground',
                  isCollapsed && 'justify-center px-2'
                )
              }
            >
              {() => (
                <>
                  <Icon className="h-4 w-4 shrink-0" />
                  {!isCollapsed && <span className="truncate">{label}</span>}
                  {isCollapsed && (
                    <div className="absolute left-full ml-2 z-50 hidden group-hover:flex items-center">
                      <div className="rounded-md bg-popover border border-border px-2.5 py-1.5 text-xs font-medium text-popover-foreground shadow-md whitespace-nowrap">
                        {label}
                      </div>
                    </div>
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>
      </ScrollArea>

      {/* ── Collapse Toggle ── */}
      <div className="border-t border-sidebar-border p-2">
        <button
          id="sidebar-collapse-btn"
          onClick={toggle}
          className={cn(
            'flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium text-sidebar-foreground/50 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground transition-colors duration-200',
            isCollapsed && 'justify-center px-2'
          )}
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <>
              <ChevronLeft className="h-4 w-4" />
              <span>Collapse</span>
            </>
          )}
        </button>
      </div>
    </aside>
  )
}
