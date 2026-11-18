
import { useRef, useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { fields } from '../data/fields'
import { attachFieldLocations } from '../data/fieldLocations'
import { attachFieldVerification } from '../data/fieldVerification'

import FieldMap from '../components/FieldMap'
import FieldImage from '../components/FieldImage'
import FieldStatus from '../components/FieldStatus'
import SiteLogo from '../components/SiteLogo'

import {
  calculateDistance,
  type Coordinates,
} from '../utils/distance'

import { getGoogleMapsUrl } from '../utils/maps'
import {
  matchesFieldSearch,
  resolveRegionQuery,
} from '../utils/fieldSearch'

import './FieldsPageNearMe.css'
import './FieldsPageCards.css'
import './FieldsPageMobile.css'
import './FieldsPageContact.css'

const allFields = attachFieldLocations(
  attachFieldVerification(fields)
)

type FieldWithDistance = {
  field: (typeof allFields)[number]
  distance: number | null
}

function FieldsPage() {
  const [searchParams, setSearchParams] = useSearchParams()

  const urlKeyword = searchParams.get('q') ?? ''

  const viewMode =
    searchParams.get('view') === 'map' ? 'map' : 'list'

  const [keyword, setKeyword] = useState(urlKeyword)
  const [appliedKeyword, setAppliedKeyword] = useState(urlKeyword)
  const [searchMessage, setSearchMessage] = useState('')
  const resultsRef = useRef<HTMLDivElement>(null)

  const [prefecture, setPrefecture] = useState('')
  const [indoorOnly, setIndoorOnly] = useState(false)
  const [rentalOnly, setRentalOnly] = useState(false)

  const [userLocation, setUserLocation] =
    useState<Coordinates | null>(null)

  const [nearMeMode, setNearMeMode] = useState(false)
  const [locationLoading, setLocationLoading] = useState(false)
  const [locationError, setLocationError] = useState('')

  const updateViewMode = (mode: 'list' | 'map') => {
    const nextParams = new URLSearchParams(searchParams)

    if (appliedKeyword.trim()) {
      nextParams.set('q', appliedKeyword.trim())
    } else {
      nextParams.delete('q')
    }

    if (mode === 'map') {
      nextParams.set('view', 'map')
    } else {
      nextParams.delete('view')
    }

    setSearchParams(nextParams, { replace: true })
  }

  const prefectures = [
    ...new Set(allFields.map((field) => field.prefecture)),
  ].sort((a, b) => a.localeCompare(b, 'ja'))

  const getDistance = (
    field: (typeof allFields)[number]
  ): number | null => {
    if (
      !nearMeMode ||
      !userLocation ||
      typeof field.latitude !== 'number' ||
      typeof field.longitude !== 'number' ||
      !Number.isFinite(field.latitude) ||
      !Number.isFinite(field.longitude) ||
      Math.abs(field.latitude) > 90 ||
      Math.abs(field.longitude) > 180
    ) {
      return null
    }

    return calculateDistance(userLocation, {
      latitude: field.latitude,
      longitude: field.longitude,
    })
  }

  const filteredFields: FieldWithDistance[] = allFields
    .filter((field) => {
      return (
        matchesFieldSearch(field, appliedKeyword) &&
        (!prefecture || field.prefecture === prefecture) &&
        (!indoorOnly || field.indoor) &&
        (!rentalOnly || field.rental === true)
      )
    })
    .map((field) => ({
      field,
      distance: getDistance(field),
    }))
    .sort((a, b) => {
      if (!nearMeMode) return 0
      if (a.distance === null && b.distance === null) return 0
      if (a.distance === null) return 1
      if (b.distance === null) return -1
      return a.distance - b.distance
    })

  const mappedFields = filteredFields.map(
    ({ field }) => field
  )

  const locatedCount = filteredFields.filter(
    ({ distance }) => distance !== null
  ).length

  const enableNearMe = () => {
    if (nearMeMode) {
      setNearMeMode(false)
      setLocationError('')
      return
    }

    if (userLocation) {
      setNearMeMode(true)
      setLocationError('')
      return
    }

    if (!navigator.geolocation) {
      setLocationError(
        'このブラウザは位置情報に対応していません。'
      )
      return
    }

    if (!window.isSecureContext) {
      setLocationError(
        '位置情報の取得にはHTTPSまたはlocalhostが必要です。'
      )
      return
    }

    setLocationLoading(true)
    setLocationError('')

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setUserLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        })

        setNearMeMode(true)
        setLocationLoading(false)
      },
      (error) => {
        setLocationLoading(false)

        if (error.code === 1) {
          setLocationError(
            '位置情報が許可されていません。ブラウザの設定を確認してください。'
          )
        } else if (error.code === 2) {
          setLocationError(
            '現在地を取得できませんでした。'
          )
        } else if (error.code === 3) {
          setLocationError(
            '位置情報の取得がタイムアウトしました。'
          )
        } else {
          setLocationError(
            '位置情報の取得中にエラーが発生しました。'
          )
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 60000,
      }
    )
  }

  const submitSearch = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    const query = keyword.trim()

    setAppliedKeyword(query)

    setSearchMessage(
      query
        ? `「${query}」を検索しました`
        : 'すべてのフィールドを表示しています'
    )

    const nextParams = new URLSearchParams(searchParams)

    if (query) {
      nextParams.set('q', query)
    } else {
      nextParams.delete('q')
    }

    setSearchParams(nextParams, { replace: true })

    if (document.activeElement instanceof HTMLElement) {
      document.activeElement.blur()
    }

    window.requestAnimationFrame(() => {
      resultsRef.current?.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      })
    })
  }

  const resetFilters = () => {
    setKeyword('')
    setAppliedKeyword('')
    setSearchMessage('')
    setSearchParams({}, { replace: true })
    setPrefecture('')
    setIndoorOnly(false)
    setRentalOnly(false)
    setNearMeMode(false)
    setLocationError('')
  }

  return (
    <div className="fields_page">
      <header className="site_header">
        <SiteLogo />

        <nav
          className="site_nav"
          aria-label="メインナビゲーション"
        >
          <Link to="/">ホーム</Link>
          <Link to="/fields">フィールド検索</Link>
          <Link to="/contact">お問い合わせ</Link>
          <Link to="/login" className="nav_login">
            ログイン
          </Link>
        </nav>
      </header>

      <main className="fields_container">
        <p className="section_eyebrow">
          EXPLORE FIELDS
        </p>

        <h1>FIND YOUR FIELD.</h1>

        <p className="fields_description">
          条件を指定して、あなたに合ったフィールドを探そう。
        </p>

        <form
          className="fields_filters"
          onSubmit={submitSearch}
          role="search"
        >
          <input
            type="search"
            aria-label="フィールドを検索"
            placeholder="フィールド名・地域で検索"
            value={keyword}
            onChange={(event) =>
              setKeyword(event.target.value)
            }
          />

          <select
            aria-label="都道府県"
            value={prefecture}
            onChange={(event) =>
              setPrefecture(event.target.value)
            }
          >
            <option value="">すべての地域</option>

            {prefectures.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>

          <button
            type="submit"
            className="fields_search_button"
          >
            検索
          </button>

          <label>
            <input
              type="checkbox"
              checked={indoorOnly}
              onChange={(event) =>
                setIndoorOnly(event.target.checked)
              }
            />
            屋内のみ
          </label>

          <label>
            <input
              type="checkbox"
              checked={rentalOnly}
              onChange={(event) =>
                setRentalOnly(event.target.checked)
              }
            />
            レンタルあり
          </label>
        </form>

        <div className="near_me_controls">
          <button
            type="button"
            className={
              nearMeMode
                ? 'near_me_button active'
                : 'near_me_button'
            }
            onClick={enableNearMe}
            disabled={locationLoading}
            aria-pressed={nearMeMode}
          >
            {locationLoading
              ? '現在地を取得中...'
              : nearMeMode
                ? '近い順モード ON'
                : '現在地から近い順に探す'}
          </button>

          {nearMeMode && (
            <p className="near_me_status">
              座標登録済み {locatedCount}件を距離順に表示
            </p>
          )}

          {locationError && (
            <p className="near_me_error" role="alert">
              {locationError}
            </p>
          )}

          {nearMeMode && (
            <p className="near_me_note">
              距離は直線距離です。
              座標未登録のフィールドは最後に表示します。
            </p>
          )}
        </div>

        <div
          className="fields_mobile_view_switch"
          role="group"
          aria-label="フィールド表示方法"
        >
          <button
            type="button"
            className={
              viewMode === 'list' ? 'active' : ''
            }
            aria-pressed={viewMode === 'list'}
            onClick={() => updateViewMode('list')}
          >
            一覧で探す
          </button>

          <button
            type="button"
            className={
              viewMode === 'map' ? 'active' : ''
            }
            aria-pressed={viewMode === 'map'}
            onClick={() => updateViewMode('map')}
          >
            地図で探す
          </button>
        </div>

        <div
          className="fields_search_feedback"
          ref={resultsRef}
          role="status"
          aria-live="polite"
        >
          <strong>
            {searchMessage || '検索結果'}
          </strong>
          <span>
            {filteredFields.length}件のフィールドが見つかりました
          </span>
        </div>

        <p className="fields_count">
          {filteredFields.length} FIELDS FOUND
        </p>

        <div
          className={
            viewMode === 'map'
              ? 'fields_map_area mobile_visible'
              : 'fields_map_area'
          }
        >
          <FieldMap
            fields={mappedFields}
            regionQuery={resolveRegionQuery(prefecture || appliedKeyword)}
          />
        </div>

        <div
          className={
            viewMode === 'list'
              ? 'fields_list_area mobile_visible'
              : 'fields_list_area'
          }
        >
          <div className="fields_grid">
            {filteredFields.map(({ field, distance }) => (
              <article
                className="field_card field_card_updated"
                key={field.id}
              >
                <Link
                  to={`/fields/${field.id}`}
                  className="field_card_main_link"
                  aria-label={`${field.name}の詳細を見る`}
                >
                  <FieldImage
                    fieldId={field.id}
                    fieldName={field.name}
                    imageUrl={field.imageUrl}
                  />

                  <div className="field_card_body">
                    <p className="field_location">
                      {field.prefecture} / {field.city}
                    </p>

                    <h2>{field.name}</h2>

                    {nearMeMode && (
                      <p className="near_me_distance">
                        {distance !== null
                          ? `現在地から約${distance.toFixed(1)}km`
                          : '距離未確認'}
                      </p>
                    )}

                    <p>{field.description}</p>

                    <div className="field_tags">
                      <span>
                        {field.indoor ? '屋内' : '屋外'}
                      </span>

                      {field.rental === true && (
                        <span>レンタルあり</span>
                      )}

                      {field.beginnerFriendly === true && (
                        <span>初心者向け</span>
                      )}
                    </div>

                    <p className="field_price">
                      {field.price === null
                        ? '料金未確認'
                        : `¥${field.price.toLocaleString()}〜`}
                    </p>

                    <FieldStatus
                      field={field}
                      variant="compact"
                    />
                  </div>
                </Link>

                <div className="field_card_actions">
                  <Link
                    to={`/fields/${field.id}`}
                    className="field_card_detail_action"
                  >
                    詳細を見る
                    <span aria-hidden="true">→</span>
                  </Link>

                  <a
                    href={getGoogleMapsUrl(field)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="field_card_map_action"
                    aria-label={`${field.name}をGoogleマップで検索`}
                  >
                    地図で確認
                    <span aria-hidden="true">↗</span>
                  </a>
                </div>
              </article>
            ))}
          </div>

          {filteredFields.length === 0 && (
            <div className="fields_empty">
              <p>条件に一致するフィールドがありません。</p>
              <button
                type="button"
                onClick={resetFilters}
              >
                条件をリセット
              </button>
            </div>
          )}
        </div>

        <section
          className="fields_contact_section"
          aria-labelledby="fields-contact-title"
        >
          <div className="fields_contact_content">
            <span className="fields_contact_eyebrow">
              SUPPORT / CONTACT
            </span>

            <h2 id="fields-contact-title">
              掲載情報について
            </h2>

            <p>
              フィールド情報の誤りや掲載内容の修正、
              サービスへのご意見・ご要望がありましたら、
              お問い合わせフォームからお知らせください。
            </p>
          </div>

          <Link
            to="/contact"
            className="fields_contact_button"
          >
            お問い合わせ・情報修正依頼
            <span aria-hidden="true">→</span>
          </Link>
        </section>
      </main>
    </div>
  )
}

export default FieldsPage
