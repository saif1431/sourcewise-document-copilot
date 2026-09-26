import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Field, FieldDescription, FieldGroup, FieldLabel } from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import { Spinner } from '@/components/ui/spinner'
import { supabase } from '@/lib/supabase'

export function SignUpPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [checkEmail, setCheckEmail] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)

    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setSubmitting(true)
    const { data, error: signUpError } = await supabase.auth.signUp({ email, password })
    setSubmitting(false)

    if (signUpError) {
      setError(signUpError.message)
      return
    }

    if (data.session) {
      navigate('/', { replace: true })
      return
    }

    setCheckEmail(true)
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Create an account</CardTitle>
          <CardDescription>Sign up for Document Copilot with your email.</CardDescription>
        </CardHeader>
        <CardContent>
          {checkEmail ? (
            <Alert>
              <AlertDescription>
                Check your email to confirm your account, then sign in.
              </AlertDescription>
            </Alert>
          ) : (
            <form onSubmit={handleSubmit}>
              <FieldGroup>
                <Field>
                  <FieldLabel htmlFor="email">Email</FieldLabel>
                  <Input
                    id="email"
                    type="email"
                    autoComplete="email"
                    required
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                  />
                </Field>
                <Field>
                  <FieldLabel htmlFor="password">Password</FieldLabel>
                  <Input
                    id="password"
                    type="password"
                    autoComplete="new-password"
                    minLength={6}
                    required
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                  />
                  <FieldDescription>At least 6 characters.</FieldDescription>
                </Field>
                <Field>
                  <FieldLabel htmlFor="confirm-password">Confirm password</FieldLabel>
                  <Input
                    id="confirm-password"
                    type="password"
                    autoComplete="new-password"
                    required
                    value={confirmPassword}
                    onChange={(event) => setConfirmPassword(event.target.value)}
                  />
                </Field>
                {error && (
                  <Alert variant="destructive">
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}
                <Button type="submit" disabled={submitting}>
                  {submitting && <Spinner data-icon="inline-start" />}
                  Sign up
                </Button>
              </FieldGroup>
            </form>
          )}
          <p className="mt-4 text-center text-sm text-muted-foreground">
            Already have an account?{' '}
            <Link to="/login" className="text-primary underline-offset-4 hover:underline">
              Sign in
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
