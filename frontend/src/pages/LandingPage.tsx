
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

function LandingPage() {
  const navigate = useNavigate()
  const [keyword, setKeyword] = useState('')

  const handleSearch = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    const query = keyword.trim()

    navigate(
      query
        ? `/fields?q=${encodeURIComponent(query)}`
        : '/fields'
    )
  }

  return (
    <div className="home_page">
      <header className="site_header">
        <Link to="/" className="site_logo">
          FIELD//BASE
        </Link>

        <nav className="site_nav" aria-label="メインナビゲーション">
          <Link to="/fields">EXPLORE</Link>
          <Link to="/login" className="nav_login">
            LOGIN
          </Link>
        </nav>
      </header>

      <main>
        <section className="hero_section">
          <div className="hero_content">
            <p className="hero_eyebrow">
              DISCOVER YOUR NEXT FIELD.
            </p>

            <h1>FIND YOUR FIELD.</h1>

            <p className="hero_description">
              あなたに合ったサバイバルゲームフィールドを、
              もっと簡単に。
            </p>

            <form
              className="hero_search"
              onSubmit={handleSearch}
              role="search"
            >
              <label htmlFor="field-search">
                フィールドを検索
              </label>

              <div className="search_controls">
                <input
                  id="field-search"
                  type="search"
                  placeholder="地域・フィールド名で検索"
                  value={keyword}
                  onChange={(event) =>
                    setKeyword(event.target.value)
                  }
                />

                <button type="submit">
                  SEARCH FIELDS
                </button>
              </div>
            </form>
          </div>
        </section>

        <section className="home_section">
          <div className="section_heading">
            <div>
              <p className="section_eyebrow">
                FIND YOUR NEXT EXPERIENCE
              </p>
              <h2>EXPLORE FIELDS</h2>
            </div>

            <Link to="/fields" className="text_link">
              VIEW ALL →
            </Link>
          </div>

          <div className="feature_grid">
            <article className="feature_card">
              <span className="feature_number">01</span>
              <h3>SEARCH</h3>
              <p>
                地域やフィールド名から、
                自分に合った場所を探す。
              </p>
            </article>

            <article className="feature_card">
              <span className="feature_number">02</span>
              <h3>COMPARE</h3>
              <p>
                料金や設備、レンタル情報を
                比較して選ぶ。
              </p>
            </article>

            <article className="feature_card">
              <span className="feature_number">03</span>
              <h3>PLAY</h3>
              <p>
                気になるフィールドを見つけて、
                次のゲームへ。
              </p>
            </article>
          </div>
        </section>
      </main>

      <footer className="site_footer">
        <span>FIELD//BASE</span>
        <span>MAKE THE FIELD PART OF LIFE.</span>
      </footer>
    </div>
  )
}

export default LandingPage
