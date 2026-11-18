
import { Link } from 'react-router-dom'

function LoginPage() {
  return (
    <main className="login_page">
      <section className="login_panel">
        <h1>FIELD//BASE</h1>

        <div className="title_line"></div>

        <p className="tagline">
          YOUR BASE IS COMING.
        </p>

        <div
          style={{
            marginTop: '40px',
            textAlign: 'center',
          }}
        >
          <p
            style={{
              fontSize: '12px',
              letterSpacing: '0.18em',
              fontWeight: 700,
              opacity: 0.65,
              marginBottom: '16px',
            }}
          >
            ACCOUNT FEATURE
          </p>

          <h2
            style={{
              fontSize: 'clamp(22px, 5vw, 32px)',
              fontWeight: 800,
              marginBottom: '20px',
            }}
          >
            アカウント機能は準備中です
          </h2>

          <p
            style={{
              fontSize: '14px',
              lineHeight: 2,
              opacity: 0.75,
              marginBottom: '32px',
            }}
          >
            FIELD//BASEをご利用いただき、
            ありがとうございます。
            <br />
            現在、ログイン・会員登録機能を
            開発しています。
            <br />
            フィールド検索は、
            アカウントなしでご利用いただけます。
          </p>

          <Link
            to="/fields"
            className="submit_button"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              textDecoration: 'none',
              minHeight: '52px',
            }}
          >
            フィールドを探す
          </Link>

          <Link
            to="/"
            style={{
              display: 'inline-block',
              marginTop: '24px',
              fontSize: '13px',
              textDecoration: 'underline',
              textUnderlineOffset: '4px',
            }}
          >
            トップページへ戻る
          </Link>
        </div>
      </section>
    </main>
  )
}

export default LoginPage
