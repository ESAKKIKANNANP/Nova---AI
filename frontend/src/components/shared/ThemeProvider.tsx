
import { useTheme } from '@/hooks/useTheme'

interface ThemeProviderProps {
  children: React.ReactNode
}

/**
 * ThemeProvider: applies the theme class to <html> on mount and
 * whenever the stored theme changes. Must wrap the entire app.
 */
export function ThemeProvider({ children }: ThemeProviderProps) {
  useTheme() // Side-effect: syncs theme → <html> class
  return <>{children}</>
}
