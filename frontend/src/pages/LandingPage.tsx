import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import SiteLogo from '../components/SiteLogo'

import './LandingPageLogo.css'
import './LandingPageContact.css'

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
        <SiteLogo />

        <nav
          className="site_nav"
          aria-label="メインナビゲーション"
        >
          <Link to="/fields">
            フィールド検索
          </Link>

          <Link to="/contact">
            お問い合わせ
          </Link>

          <Link to="/login" className="nav_login">
            ログイン
          </Link>
        </nav>
      </header>

      <main>
        <section className="hero_section">
          <div className="hero_content">
            <div className="hero_brand">
              <img
                src="/fieldbase-mark.png"
                alt="FIELD//BASE カマキリのロゴ"
                className="hero_brand_image"
              />

              <span className="hero_brand_name">
                FIELD<span>//</span>BASE
              </span>
            </div>

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
                  検索
                </button>
              </div>
            </form>

            <div className="hero_contact">
              <span>
                掲載情報の間違いやご意見はこちら
              </span>

              <Link to="/contact">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <rect
                    x="3"
                    y="5"
                    width="18"
                    height="14"
                    rx="2"
                  />
                  <path d="m3 7 9 7 9-7" />
                </svg>

                お問い合わせ・情報修正依頼
                <span aria-hidden="true">→</span>
              </Link>
            </div>
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
              すべてのフィールドを見る →
            </Link>
          </div>

          <div className="feature_grid">
            <article className="feature_card">
              <span className="feature_number">01</span>
              <h3>検索</h3>
              <p>
                地域やフィールド名から、
                自分に合った場所を探す。
              </p>
            </article>

            <article className="feature_card">
              <span className="feature_number">02</span>
              <h3>比較する</h3>
              <p>
                料金や設備、レンタル情報を
                比較して選ぶ。
              </p>
            </article>

            <article className="feature_card">
              <span className="feature_number">03</span>
              <h3>楽しむ</h3>
              <p>
                気になるフィールドを見つけて、
                次のゲームへ。
              </p>
            </article>
          </div>
        </section>
      </main>

      <footer className="site_footer">
        <div className="footer_brand">
          <img
            src="/fieldbase-mark.png"
            alt=""
            className="footer_brand_image"
          />
          <span>FIELD//BASE</span>
        </div>

        <span>MAKE THE FIELD PART OF LIFE.</span>

        <Link to="/contact">
          お問い合わせ
        </Link>
      </footer>
    </div>
  )
}

export default LandingPage