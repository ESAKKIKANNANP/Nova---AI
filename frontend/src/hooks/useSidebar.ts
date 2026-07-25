import { useUIStore } from '@/store/uiStore'

/**
 * Convenience hook for sidebar collapse/expand state.
 */
export function useSidebar() {
  const { sidebarCollapsed, sidebarMobileOpen, toggleSidebar, setSidebarCollapsed, setSidebarMobileOpen } =
    useUIStore()

  return {
    isCollapsed: sidebarCollapsed,
    isMobileOpen: sidebarMobileOpen,
    toggle: toggleSidebar,
    collapse: () => setSidebarCollapsed(true),
    expand: () => setSidebarCollapsed(false),
    setMobileOpen: setSidebarMobileOpen,
  }
}
