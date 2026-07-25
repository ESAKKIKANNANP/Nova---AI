import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Navbar } from './Navbar'
import { useSidebar } from '@/hooks/useSidebar'
import { cn } from '@/utils/cn'

/**
 * AppLayout: the root shell for all authenticated pages.
 * Composes the Sidebar + Navbar + main content area.
 */
export function AppLayout() {
  const { isCollapsed } = useSidebar()

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Desktop sidebar */}
      <Sidebar />

      {/* Main content column */}
      <div
        className={cn(
          'flex flex-1 flex-col overflow-hidden transition-all duration-300',
          isCollapsed ? 'md:ml-0' : 'md:ml-0'
        )}
      >
        <Navbar />

        {/* Scrollable page area */}
        <main className="flex-1 overflow-y-auto">
          <div className="container mx-auto max-w-7xl p-4 md:p-6 lg:p-8 animate-fade-in">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
