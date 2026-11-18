
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

const DIRECTORY_SOURCE =
  'https://sightin.jp/field/map/?area=kanto'

function isValidWebUrl(value: string): boolean {
  try {
    const url = new URL(value)

    return (
      url.protocol === 'https:' ||
      url.protocol === 'http:'
    )
  } catch {
    return false
  }
}

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

  const hasWebsite = isValidWebUrl(field.website)

  const hasDetailedAddress =
    field.address.trim() !== '' &&
    !field.address.includes('未確認')

  const hasCoordinates =
    typeof field.latitude === 'number' &&
    typeof field.longitude === 'number' &&
    Number.isFinite(field.latitude) &&
    Number.isFinite(field.longitude) &&
    Math.abs(field.latitude) <= 90 &&
    Math.abs(field.longitude) <= 180

  const canShowDirections =
    hasDetailedAddress || hasCoordinates

  const hasVerificationDate =
    typeof field.verifiedAt === 'string' &&
    /^\d{4}-\d{2}-\d{2}$/.test(field.verifiedAt)

  const hasSourceUrl =
    isValidWebUrl(field.sourceUrl) &&
    field.sourceUrl !== DIRECTORY_SOURCE

  const correctionUrl =
    `/contact?type=correction&field=${encodeURIComponent(field.name)}`

  const addressLabel = hasDetailedAddress
    ? field.address
    : `${field.prefecture}${field.city}（詳細住所未確認）`

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
                  <dd>{addressLabel}</dd>
                </div>

                <div>
                  <dt>フィールドタイプ</dt>
                  <dd>
                    {field.indoor ? '屋内' : '屋外'}
                  </dd>
                </div>

                <div>
                  <dt>料金</dt>
                  <dd
                    style={
                      field.price === null
                        ? {
                            fontSize: '14px',
                            fontWeight: 600,
                            color: '#64717b',
                          }
                        : undefined
                    }
                  >
                    {field.price === null
                      ? '料金未確認'
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
                {addressLabel}
              </p>

              {canShowDirections ? (
                <>
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
                </>
              ) : (
                <p className="field_detail_muted">
                  正確な経路を案内するための
                  位置情報を準備中です。
                </p>
              )}

              {!hasDetailedAddress && (
                <p className="field_detail_notice">
                  詳細住所は未確認です。
                  {hasCoordinates
                    ? ' 地図上の位置は参考情報です。訪問前に施設の所在地をご確認ください。'
                    : ' 正確な所在地が確認できるまで、経路案内を表示していません。'}
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
                  {hasVerificationDate
                    ? field.verifiedAt
                    : '情報確認前'}
                </strong>
              </div>

              {hasSourceUrl && (
                <a
                  href={field.sourceUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="field_detail_source"
                >
                  情報の参照元 ↗
                </a>
              )}

              {!hasVerificationDate && (
                <p className="field_detail_notice">
                  このフィールドの掲載情報は、
                  個別の確認日が登録されていません。
                </p>
              )}

              <p className="field_detail_notice">
                掲載情報は変更される場合があります。
                営業状況・料金・予約条件は訪問前に
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

      {canShowDirections && (
        <div className="field_detail_mobile_action">
          <a
            href={getGoogleMapsDirectionsUrl(field)}
            target="_blank"
            rel="noopener noreferrer"
          >
            経路案内を開く ↗
          </a>
        </div>
      )}
    </div>
  )
}

export default FieldDetailPage
