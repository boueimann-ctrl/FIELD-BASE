import { useNavigate } from 'react-router-dom'

function LandingPage() {
  const navigate = useNavigate()

  return (
    <main className="login_page">
      <section className="login_panel">
        <h1>FIELD//BASE</h1>

        <div className="title_line"></div>

        <p className="tagline">
          FIND YOUR FIELD.
        </p>

        <div className="login_actions">
          <button
            className="login_button"
            onClick={() => navigate('/login')}
          >
            FB // LOGIN
            <span className="action_line"></span>
          </button>

          <button className="register_button">
            FB // REGISTER
            <span className="action_line"></span>
          </button>
        </div>
      </section>
    </main>
  )
}

export default LandingPage