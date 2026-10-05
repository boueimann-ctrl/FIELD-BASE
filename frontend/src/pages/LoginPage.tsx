import { useState, type FormEvent } from 'react'

function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [emailError, setEmailError] = useState('')

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
 if (email === '') {
  setEmailError('EMAIL IS REQUIRED')
} else if (!email.includes('@')) {
  setEmailError('INVALID EMAIL')
} else {
  setEmailError('')
}


if (password === '') {
  setPassword('PASSWORD IS REQUIRED')
} else if (!password.includes('6')){
  setPassword('PASSWORD IS REQUIRED')
}else{
  setPassword('')
}

  return (
    <main className="login_page">
      <section className="login_panel">

        <h1>FIELD//BASE</h1>

        <div className="title_line"></div>

        <p className="tagline">
          LOGIN TO YOUR BASE.
        </p>

        <form className="login_form" onSubmit={handleSubmit}>

          <div className="form_group">
            <label htmlFor="email">EMAIL</label>

            <input
              id="email"
              type="email"
              placeholder="your@email.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />

            <p>{emailError}</p>
          </div>

          <div className="form_group">
            <label htmlFor="password">PASSWORD</label>

            <input
              id="password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
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