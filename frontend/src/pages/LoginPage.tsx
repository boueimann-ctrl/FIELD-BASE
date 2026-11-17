
import { useState, type FormEvent } from 'react'

function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [emailError, setEmailError] = useState('')
  const [passwordError, setPasswordError] = useState('')

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    let isValid = true

    if (email.trim() === '') {
      setEmailError('EMAIL IS REQUIRED')
      isValid = false
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setEmailError('INVALID EMAIL')
      isValid = false
    } else {
      setEmailError('')
    }

    if (password === '') {
      setPasswordError('PASSWORD IS REQUIRED')
      isValid = false
    } else if (password.length < 6) {
      setPasswordError('PASSWORD MUST BE AT LEAST 6 CHARACTERS')
      isValid = false
    } else {
      setPasswordError('')
    }

    if (!isValid) return

    // Firebase Authenticationとの連携は次の工程で実装
    console.log('Login form validation successful')
  }

  return (
    <main className="login_page">
      <section className="login_panel">
        <h1>FIELD//BASE</h1>

        <div className="title_line"></div>

        <p className="tagline">LOGIN TO YOUR BASE.</p>

        <form className="login_form" onSubmit={handleSubmit} noValidate>
          <div className="form_group">
            <label htmlFor="email">EMAIL</label>

            <input
              id="email"
              type="email"
              placeholder="your@email.com"
              autoComplete="email"
              value={email}
              aria-invalid={!!emailError}
              aria-describedby={emailError ? 'email-error' : undefined}
              onChange={(event) => {
                setEmail(event.target.value)
                setEmailError('')
              }}
            />

            {emailError && (
              <p id="email-error" role="alert">{emailError}</p>
            )}
          </div>

          <div className="form_group">
            <label htmlFor="password">PASSWORD</label>

            <input
              id="password"
              type="password"
              placeholder="••••••••"
              autoComplete="current-password"
              value={password}
              aria-invalid={!!passwordError}
              aria-describedby={passwordError ? 'password-error' : undefined}
              onChange={(event) => {
                setPassword(event.target.value)
                setPasswordError('')
              }}
            />

            {passwordError && (
              <p id="password-error" role="alert">{passwordError}</p>
            )}
          </div>

          <button type="submit" className="submit_button">
            LOGIN
            <span className="action_line"></span>
          </button>
        </form>
      </section>
    </main>
  )
}

export default LoginPage
