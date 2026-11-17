
import { Link, useParams } from 'react-router-dom'
import { fields } from '../data/fields'

function FieldDetailPage() {
  const { id } = useParams<{ id: string }>()

  const field = fields.find((item) => item.id === id)

  if (!field) {
    return (
      <main className="field_not_found">
        <h1>FIELD NOT FOUND.</h1>
        <p>指定されたフィールドは見つかりませんでした。</p>
        <Link to="/fields">← フィールド一覧に戻る</Link>
      </main>
    )
  }

  return (
    <div className="field_detail_page">
      <header className="site_header">
        <Link to="/" className="site_logo">
          FIELD//BASE
        </Link>

        <nav
          className="site_nav"
          aria-label="メインナビゲーション"
        >
          <Link to="/fields">EXPLORE</Link>
          <Link to="/login" className="nav_login">
            LOGIN
          </Link>
        </nav>
      </header>

      <main className="field_detail_container">
        <Link to="/fields" className="detail_back">
          ← BACK TO FIELDS
        </Link>

        <div className="detail_heading">
          <p className="section_eyebrow">
            FIELD INFORMATION
          </p>

          <h1>{field.name}</h1>

          <p className="detail_location">
            {field.prefecture} / {field.city}
          </p>
        </div>

        <div className="detail_hero">
          {field.imageUrl ? (
            <img
              src={field.imageUrl}
              alt={`${field.name}のフィールド写真`}
            />
          ) : (
            <span>FIELD//BASE</span>
          )}
        </div>

        <div className="detail_layout">
          <section className="detail_main">
            <h2>ABOUT THIS FIELD.</h2>

            <p className="detail_description">
              {field.description}
            </p>

            <h2>FIELD INFORMATION.</h2>

            <div className="detail_info_grid">
              <div>
                <span>LOCATION</span>
                <strong>
                  {field.prefecture} {field.city}
                </strong>
              </div>

              <div>
                <span>FIELD TYPE</span>
                <strong>
                  {field.indoor ? '屋内' : '屋外'}
                </strong>
              </div>

              <div>
                <span>RENTAL</span>
                <strong>
                  {field.rental ? 'あり' : 'なし'}
                </strong>
              </div>

              <div>
                <span>BEGINNER FRIENDLY</span>
                <strong>
                  {field.beginnerFriendly ? '対応あり' : '未確認'}
                </strong>
              </div>
            </div>

            <h2>ACCESS.</h2>

            <p className="detail_address">
              {field.address}
            </p>

            {field.address !== 'デモ用データ' && (
              <a
                className="detail_map_link"
                href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(field.address)}`}
                target="_blank"
                rel="noopener noreferrer"
              >
                GOOGLE MAPSで確認 →
              </a>
            )}
          </section>

          <aside className="detail_sidebar">
            <div className="detail_price_card">
              <p>ENTRY PRICE</p>

              <strong>
                {field.price === null
                  ? '料金未確認'
                  : `¥${field.price.toLocaleString()}〜`}
              </strong>

              <span>
                料金はプランや開催日によって異なる場合があります。
              </span>

              {field.website ? (
                <a
                  href={field.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="detail_website_button"
                >
                  OFFICIAL WEBSITE →
                </a>
              ) : (
                <span className="detail_website_disabled">
                  公式サイト未登録
                </span>
              )}
            </div>
          </aside>
        </div>
      </main>

      <footer className="site_footer">
        <span>FIELD//BASE</span>
        <span>MAKE THE FIELD PART OF LIFE.</span>
      </footer>
    </div>
  )
}

export default FieldDetailPage
