import type { LucideIcon } from 'lucide-react'
import { TrendingDown, TrendingUp } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/utils/cn'

interface StatCardProps {
  title: string
  value: string | number
  delta?: number
  deltaLabel?: string
  icon: LucideIcon
  iconColor?: string
  iconBg?: string
  loading?: boolean
  className?: string
}

/**
 * KPI metric card with icon, value, and optional delta indicator.
 */
export function StatCard({
  title,
  value,
  delta,
  deltaLabel = 'vs last month',
  icon: Icon,
  iconColor = 'text-blue-400',
  iconBg = 'bg-blue-500/10',
  loading = false,
  className,
}: StatCardProps) {
  const isPositive = delta !== undefined && delta >= 0

  if (loading) {
    return (
      <Card className={cn('p-6', className)}>
        <div className="flex items-center justify-between">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-10 w-10 rounded-lg" />
        </div>
        <Skeleton className="mt-4 h-8 w-32" />
        <Skeleton className="mt-2 h-3 w-20" />
      </Card>
    )
  }

  return (
    <Card
      className={cn(
        'relative overflow-hidden p-6 transition-all duration-300 hover:shadow-lg hover:-translate-y-0.5 group',
        className
      )}
    >
      {/* Subtle gradient accent */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/[0.02] to-transparent pointer-events-none" />

      <div className="flex items-start justify-between">
        <p className="text-sm font-medium text-muted-foreground">{title}</p>
        <div className={cn('flex h-10 w-10 items-center justify-center rounded-lg', iconBg)}>
          <Icon className={cn('h-5 w-5', iconColor)} />
        </div>
      </div>

      <div className="mt-3">
        <p className="text-3xl font-bold tracking-tight text-foreground">{value}</p>
        {delta !== undefined && (
          <div className="mt-1 flex items-center gap-1 text-xs">
            {isPositive ? (
              <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />
            ) : (
              <TrendingDown className="h-3.5 w-3.5 text-red-400" />
            )}
            <span className={cn(isPositive ? 'text-emerald-400' : 'text-red-400', 'font-semibold')}>
              {isPositive ? '+' : ''}
              {delta}%
            </span>
            <span className="text-muted-foreground">{deltaLabel}</span>
          </div>
        )}
      </div>
    </Card>
  )
}
