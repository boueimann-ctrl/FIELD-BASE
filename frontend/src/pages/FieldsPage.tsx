
import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { fields } from '../data/fields'

function FieldsPage() {
  const [searchParams] = useSearchParams()

  const [keyword, setKeyword] = useState(
    () => searchParams.get('q') ?? ''
  )
  const [prefecture, setPrefecture] = useState('')
  const [indoorOnly, setIndoorOnly] = useState(false)
  const [rentalOnly, setRentalOnly] = useState(false)

  const filteredFields = fields.filter((field) => {
    const searchText = [
      field.name,
      field.prefecture,
      field.city,
      field.description,
    ].join(' ').toLowerCase()

    return (
      searchText.includes(keyword.trim().toLowerCase()) &&
      (!prefecture || field.prefecture === prefecture) &&
      (!indoorOnly || field.indoor) &&
      (!rentalOnly || field.rental)
    )
  })

  return (
    <div className="fields_page">
      <header className="site_header">
        <Link to="/" className="site_logo">
          FIELD//BASE
        </Link>

        <nav className="site_nav">
          <Link to="/">HOME</Link>
          <Link to="/login" className="nav_login">
            LOGIN
          </Link>
        </nav>
      </header>

      <main className="fields_container">
        <p className="section_eyebrow">EXPLORE FIELDS</p>
        <h1>FIND YOUR FIELD.</h1>

        <p className="fields_description">
          条件を指定して、あなたに合ったフィールドを探そう。
        </p>

        <div className="fields_filters">
          <input
            type="search"
            aria-label="フィールドを検索"
            placeholder="フィールド名・地域で検索"
            value={keyword}
            onChange={(event) => setKeyword(event.target.value)}
          />

          <select
            aria-label="都道府県"
            value={prefecture}
            onChange={(event) => setPrefecture(event.target.value)}
          >
            <option value="">すべての地域</option>
            {[...new Set(fields.map((f) => f.prefecture))].map(
              (name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              )
            )}
          </select>

          <label>
            <input
              type="checkbox"
              checked={indoorOnly}
              onChange={(event) => setIndoorOnly(event.target.checked)}
            />
            屋内のみ
          </label>

          <label>
            <input
              type="checkbox"
              checked={rentalOnly}
              onChange={(event) => setRentalOnly(event.target.checked)}
            />
            レンタルあり
          </label>
        </div>

        <p className="fields_count">
          {filteredFields.length} FIELDS FOUND
        </p>

        <div className="fields_grid">
          {filteredFields.map((field) => (
            <Link
              to={`/fields/${field.id}`}
              className="field_card_link"
              key={field.id}
            >
              <article className="field_card">
                <div className="field_image_placeholder">
                  FIELD//BASE
                </div>

                <div className="field_card_body">
                  <p className="field_location">
                    {field.prefecture} / {field.city}
                  </p>

                  <h2>{field.name}</h2>
                  <p>{field.description}</p>

                  <div className="field_tags">
                    <span>{field.indoor ? '屋内' : '屋外'}</span>
                    {field.rental && <span>レンタルあり</span>}
                    {field.beginnerFriendly && (
                      <span>初心者向け</span>
                    )}
                  </div>

                  <p className="field_price">
                    {field.price === null
                      ? '料金未確認'
                      : `¥${field.price.toLocaleString()}〜`}
                  </p>

                  <span className="field_view_detail">
                    VIEW DETAILS →
                  </span>
                </div>
              </article>
            </Link>
          ))}
        </div>

        {filteredFields.length === 0 && (
          <p className="fields_empty">
            条件に一致するフィールドがありません。
          </p>
        )}
      </main>
    </div>
  )
}

export default FieldsPage
