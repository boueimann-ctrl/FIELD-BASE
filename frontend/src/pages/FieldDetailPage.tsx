import { Link, useParams } from 'react-router-dom'

import { fields } from '../data/fields'
import { attachFieldLocations } from '../data/fieldLocations'
import { attachFieldVerification } from '../data/fieldVerification'

import FieldImage from '../components/FieldImage'
import FieldStatus from '../components/FieldStatus'
import SiteLogo from '../components/SiteLogo'

import {
  getGoogleMapsUrl,
  getGoogleMapsDirectionsUrl,
} from '../utils/maps'

import './FieldDetailPage.css'
import './FieldDetailMobile.css'

const allFields = attachFieldLocations(
  attachFieldVerification(fields)
)

function FieldDetailPage() {
  const { id } = useParams<{ id: string }>()

  const field = allFields.find((item) => item.id === id)

  if (!field) {
    return (
      <div className="field_detail_page">
        <main className="field_detail_container">
          <Link to="/fields" className="field_detail_back">
            ← フィールド一覧に戻る
          </Link>

          <h1>フィールドが見つかりません</h1>

          <p>URLが正しいか確認してください。</p>
        </main>
      </div>
    )
  }

  const hasWebsite = /^https?:\/\//i.test(field.website)

  const hasDetailedAddress =
    field.address.trim() !== '' &&
    !field.address.includes('詳細住所未確認')

  const correctionUrl =
    `/contact?type=correction&field=${encodeURIComponent(field.name)}`

  return (
    <div className="field_detail_page">
      <header className="site_header">
        <SiteLogo />

        <nav className="site_nav">
          <Link to="/">HOME</Link>
          <Link to="/fields">FIELDS</Link>
          <Link to="/contact">CONTACT</Link>
          <Link to="/login" className="nav_login">
            LOGIN
          </Link>
        </nav>
      </header>

      <main className="field_detail_container">
        <Link to="/fields" className="field_detail_back">
          ← フィールド一覧に戻る
        </Link>

        <div className="field_detail_heading">
          <p className="field_detail_eyebrow">
            FIELD INFORMATION
          </p>

          <h1>{field.name}</h1>

          <p className="field_detail_location">
            {field.prefecture} / {field.city}
          </p>
        </div>

        <div className="field_detail_layout">
          <div className="field_detail_primary">
            <div className="field_detail_hero">
              <FieldImage
                fieldId={field.id}
                fieldName={field.name}
                imageUrl={field.imageUrl}
                variant="detail"
              />
            </div>

            <section className="field_detail_section">
              <h2>フィールドについて</h2>
              <p>{field.description}</p>
            </section>

            <section className="field_detail_section">
              <h2>基本情報</h2>

              <dl className="field_detail_info">
                <div>
                  <dt>所在地</dt>
                  <dd>{field.address}</dd>
                </div>

                <div>
                  <dt>フィールドタイプ</dt>
                  <dd>{field.indoor ? '屋内' : '屋外'}</dd>
                </div>

                <div>
                  <dt>料金</dt>
                  <dd>
                    {field.price === null
                      ? '未確認'
                      : `¥${field.price.toLocaleString()}〜`}
                  </dd>
                </div>

                <div>
                  <dt>レンタル</dt>
                  <dd>
                    {field.rental === null
                      ? '未確認'
                      : field.rental
                        ? 'あり'
                        : 'なし'}
                  </dd>
                </div>

                <div>
                  <dt>初心者向け情報</dt>
                  <dd>
                    {field.beginnerFriendly === null
                      ? '未確認'
                      : field.beginnerFriendly
                        ? 'あり'
                        : '未設定'}
                  </dd>
                </div>
              </dl>
            </section>

            <FieldStatus field={field} variant="full" />
          </div>

          <aside className="field_detail_sidebar">
            <section className="field_detail_panel">
              <p className="field_detail_panel_label">
                ACCESS
              </p>

              <h2>アクセス・経路案内</h2>

              <p className="field_detail_address">
                {field.address}
              </p>

              <a
                href={getGoogleMapsDirectionsUrl(field)}
                target="_blank"
                rel="noopener noreferrer"
                className="field_detail_button primary"
              >
                経路を調べる ↗
              </a>

              <a
                href={getGoogleMapsUrl(field)}
                target="_blank"
                rel="noopener noreferrer"
                className="field_detail_button secondary"
              >
                Googleマップで確認 ↗
              </a>

              {!hasDetailedAddress && (
                <p className="field_detail_notice">
                  詳細住所は未確認です。
                  地図の検索結果を確認してください。
                </p>
              )}
            </section>

            <section className="field_detail_panel">
              <p className="field_detail_panel_label">
                OFFICIAL INFORMATION
              </p>

              <h2>公式情報</h2>

              {hasWebsite ? (
                <a
                  href={field.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="field_detail_button secondary"
                >
                  公式サイトを見る ↗
                </a>
              ) : (
                <p className="field_detail_muted">
                  公式サイトは未登録です。
                </p>
              )}

              <div className="field_detail_verification">
                <span>情報確認日</span>
                <strong>
                  {field.verifiedAt ?? '未確認'}
                </strong>
              </div>

              {field.sourceUrl && (
                <a
                  href={field.sourceUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="field_detail_source"
                >
                  情報の参照元 ↗
                </a>
              )}

              <p className="field_detail_notice">
                掲載情報は変更される場合があります。
                営業日・料金・予約条件は訪問前に
                施設へご確認ください。
              </p>

              <Link
                to={correctionUrl}
                className="field_detail_button secondary"
              >
                掲載情報の修正を依頼する →
              </Link>
            </section>
          </aside>
        </div>
      </main>

      <div className="field_detail_mobile_action">
        <a
          href={getGoogleMapsDirectionsUrl(field)}
          target="_blank"
          rel="noopener noreferrer"
        >
          経路案内を開く ↗
        </a>
      </div>
    </div>
  )
}

export default FieldDetailPage