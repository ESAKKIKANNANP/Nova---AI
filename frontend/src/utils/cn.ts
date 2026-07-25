import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Merges Tailwind CSS class names intelligently.
 * Uses clsx for conditional classes and tailwind-merge to
 * resolve conflicting Tailwind utilities (e.g. p-2 vs p-4).
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
