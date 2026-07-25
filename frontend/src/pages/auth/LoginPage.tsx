import { Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Eye, EyeOff, Mail, Lock, Sparkles } from 'lucide-react'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { useAuth } from '@/hooks/useAuth'

// ─── Validation Schema ────────────────────────────────────────────

const loginSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
})

type LoginFormValues = z.infer<typeof loginSchema>

// ─── Component ───────────────────────────────────────────────────

export default function LoginPage() {
  const { login, isLoggingIn } = useAuth()
  const [showPassword, setShowPassword] = useState(false)

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  })

  const onSubmit = (values: LoginFormValues) => {
    login(values)
  }

  return (
    <div className="min-h-screen flex bg-background bg-grid">
      {/* ── Left Panel (decorative) ── */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-gradient-to-br from-blue-950 via-indigo-950 to-violet-950">
        {/* Glowing orbs */}
        <div className="absolute top-1/4 left-1/4 h-64 w-64 rounded-full bg-blue-600/20 blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 h-48 w-48 rounded-full bg-violet-600/20 blur-3xl" />

        <div className="relative z-10 flex flex-col justify-center px-16">
          <div className="flex items-center gap-3 mb-12">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl gradient-primary shadow-lg shadow-blue-500/30">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-bold text-white">AutoDS</span>
          </div>

          <h1 className="text-4xl font-bold text-white leading-tight mb-4">
            Autonomous Data
            <br />
            <span className="gradient-text">Science Platform</span>
          </h1>
          <p className="text-blue-200/70 text-lg leading-relaxed max-w-sm">
            Automate your entire data science pipeline — from ingestion to deployment — with AI agents.
          </p>

          <div className="mt-12 grid grid-cols-2 gap-4">
            {[
              { label: 'Active Agents', value: '24' },
              { label: 'Models Deployed', value: '128' },
              { label: 'Experiments Run', value: '1.4K' },
              { label: 'Datasets Processed', value: '340' },
            ].map(({ label, value }) => (
              <div key={label} className="rounded-xl border border-white/10 bg-white/5 p-4">
                <p className="text-2xl font-bold text-white">{value}</p>
                <p className="text-xs text-blue-200/60 mt-0.5">{label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Right Panel (form) ── */}
      <div className="flex flex-1 items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm space-y-8 animate-fade-in">
          {/* Mobile logo */}
          <div className="flex lg:hidden items-center gap-2 justify-center mb-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg gradient-primary">
              <Sparkles className="h-4 w-4 text-white" />
            </div>
            <span className="text-lg font-bold">AutoDS</span>
          </div>

          <div>
            <h2 className="text-2xl font-bold tracking-tight">Welcome back</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Sign in to your account to continue
            </p>
          </div>

          <Form {...form}>
            <form
              id="login-form"
              onSubmit={form.handleSubmit(onSubmit)}
              className="space-y-4"
            >
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email address</FormLabel>
                    <FormControl>
                      <Input
                        id="login-email"
                        type="email"
                        placeholder="you@company.com"
                        autoComplete="email"
                        leftIcon={<Mail className="h-4 w-4" />}
                        error={!!form.formState.errors.email}
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <div className="flex items-center justify-between">
                      <FormLabel>Password</FormLabel>
                      <button
                        type="button"
                        className="text-xs text-primary hover:underline"
                        tabIndex={-1}
                      >
                        Forgot password?
                      </button>
                    </div>
                    <FormControl>
                      <Input
                        id="login-password"
                        type={showPassword ? 'text' : 'password'}
                        placeholder="••••••••"
                        autoComplete="current-password"
                        leftIcon={<Lock className="h-4 w-4" />}
                        rightIcon={
                          <button
                            type="button"
                            onClick={() => setShowPassword((v) => !v)}
                            className="text-muted-foreground hover:text-foreground transition-colors"
                            aria-label={showPassword ? 'Hide password' : 'Show password'}
                          >
                            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                          </button>
                        }
                        error={!!form.formState.errors.password}
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <Button
                id="login-submit-btn"
                type="submit"
                className="w-full"
                variant="gradient"
                size="lg"
                loading={isLoggingIn}
              >
                Sign in
              </Button>
            </form>
          </Form>

          <div className="relative flex py-2 items-center">
            <div className="flex-grow border-t border-neutral-800"></div>
            <span className="flex-shrink mx-4 text-neutral-500 text-xs uppercase tracking-wider">or</span>
            <div className="flex-grow border-t border-neutral-800"></div>
          </div>

          <Button
            type="button"
            variant="outline"
            className="w-full border-neutral-850 bg-neutral-900/40 hover:bg-neutral-800/40 text-neutral-200 flex items-center justify-center gap-2 py-5"
            onClick={() => {
              window.location.href = "https://accounts.google.com/o/oauth2/v2/auth";
            }}
          >
            <svg className="h-4 w-4" viewBox="0 0 24 24" width="24" height="24" xmlns="http://www.w3.org/2000/svg">
              <g transform="matrix(1, 0, 0, 1, 0, 0)">
                <path d="M21.35,11.1H12v2.7h5.38c-0.24,1.28 -0.96,2.37 -2.04,3.1l3.12,2.42c1.84,-1.7 2.89,-4.2 2.89,-7.1C21.35,11.83 21.27,11.45 21.35,11.1z" fill="#4285F4" />
                <path d="M12,21c2.43,0 4.47,-0.8 5.96,-2.18l-3.12,-2.42c-0.87,0.59 -1.98,0.94 -2.84,0.94 -2.34,0 -4.32,-1.58 -5.03,-3.71L3.75,16.4C5.23,19.3 8.35,21 12,21z" fill="#34A853" />
                <path d="M6.97,13.63c-0.18,-0.54 -0.28,-1.11 -0.28,-1.7s0.1,-1.16 0.28,-1.7L3.75,7.8C3.07,9.15 2.7,10.66 2.7,12.25s0.37,3.1 1.05,4.45L6.97,13.63z" fill="#FBBC05" />
                <path d="M12,6.38c1.32,0 2.5,0.45 3.44,1.35l2.58,-2.58C16.46,3.64 14.43,3 12,3 8.35,3 5.23,4.7 3.75,7.6L6.97,10.12C7.68,7.99 9.66,6.38 12,6.38z" fill="#EA4335" />
              </g>
            </svg>
            Continue with Google
          </Button>

          <p className="text-center text-sm text-muted-foreground">
            Don't have an account?{' '}
            <Link
              to="/register"
              id="go-to-register-link"
              className="font-semibold text-primary hover:underline"
            >
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
