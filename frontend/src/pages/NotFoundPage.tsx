import { Link } from 'react-router-dom'
import { Home, ArrowLeft, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function NotFoundPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background bg-grid px-6">
      <div className="text-center space-y-6 animate-fade-in">
        {/* Glowing icon */}
        <div className="flex justify-center">
          <div className="relative flex h-20 w-20 items-center justify-center rounded-2xl gradient-primary shadow-2xl shadow-blue-500/30">
            <Sparkles className="h-10 w-10 text-white" />
            <div className="absolute inset-0 rounded-2xl bg-white/10 blur-sm" />
          </div>
        </div>

        <div className="space-y-2">
          <p className="text-8xl font-black tracking-tight gradient-text">404</p>
          <h1 className="text-2xl font-bold text-foreground">Page not found</h1>
          <p className="text-muted-foreground max-w-sm mx-auto">
            The page you're looking for doesn't exist or has been moved. Let's get you back on track.
          </p>
        </div>

        <div className="flex items-center justify-center gap-3 flex-wrap">
          <Button id="go-back-btn" variant="outline" onClick={() => window.history.back()}>
            <ArrowLeft className="h-4 w-4" />
            Go back
          </Button>
          <Button id="go-home-btn" variant="gradient" asChild>
            <Link to="/">
              <Home className="h-4 w-4" />
              Dashboard
            </Link>
          </Button>
        </div>
      </div>
    </div>
  )
}
