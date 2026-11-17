
import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { fields } from '../data/fields'
import { attachFieldLocations } from '../data/fieldLocations'
import { attachFieldVerification } from '../data/fieldVerification'
import FieldMap from '../components/FieldMap'

import {
  calculateDistance,
  type Coordinates,
} from '../utils/distance'
import { getGoogleMapsUrl } from '../utils/maps'

import './FieldsPageNearMe.css'
import './FieldsPageCards.css'

const allFields = attachFieldLocations(
  attachFieldVerification(fields)
)

type FieldWithDistance = {
  field: (typeof allFields)[number]
  distance: number | null
}

function FieldsPage() {
  const [searchParams] = useSearchParams()

  const [keyword, setKeyword] = useState(
    () => searchParams.get('q') ?? ''
  )
  const [prefecture, setPrefecture] = useState('')
  const [indoorOnly, setIndoorOnly] = useState(false)
  const [rentalOnly, setRentalOnly] = useState(false)

  const [userLocation, setUserLocation] =
    useState<Coordinates | null>(null)

  const [nearMeMode, setNearMeMode] = useState(false)
  const [locationLoading, setLocationLoading] = useState(false)
  const [locationError, setLocationError] = useState('')

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
      const searchText = [
        field.name,
        field.prefecture,
        field.city,
        field.address,
        field.description,
      ]
        .join(' ')
        .toLowerCase()

      return (
        searchText.includes(keyword.trim().toLowerCase()) &&
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

  const resetFilters = () => {
    setKeyword('')
    setPrefecture('')
    setIndoorOnly(false)
    setRentalOnly(false)
    setNearMeMode(false)
    setLocationError('')
  }

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
        <p className="section_eyebrow">
          EXPLORE FIELDS
        </p>

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
        </div>

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

        <p className="fields_count">
          {filteredFields.length} FIELDS FOUND
        </p>

        <FieldMap fields={mappedFields} />

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
                <div className="field_image_placeholder">
                  FIELD//BASE
                </div>

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
            <button type="button" onClick={resetFilters}>
              条件をリセット
            </button>
          </div>
        )}
      </main>
    </div>
  )
}

export default FieldsPage
