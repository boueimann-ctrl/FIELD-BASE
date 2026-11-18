
import { useEffect, useMemo } from 'react'
import {
  MapContainer,
  Marker,
  Popup,
  TileLayer,
  useMap,
} from 'react-leaflet'
import { Link } from 'react-router-dom'
import L from 'leaflet'

import type { Field } from '../types/field'

import 'leaflet/dist/leaflet.css'
import './FieldMap.css'

type FieldMapProps = {
  fields: Field[]
  regionQuery?: string
}

type MappableField = Field & {
  latitude: number
  longitude: number
}

const markerIcon = L.icon({
  iconUrl:
    'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl:
    'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl:
    'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

function hasCoordinates(
  field: Field
): field is MappableField {
  return (
    typeof field.latitude === 'number' &&
    typeof field.longitude === 'number' &&
    Number.isFinite(field.latitude) &&
    Number.isFinite(field.longitude) &&
    Math.abs(field.latitude) <= 90 &&
    Math.abs(field.longitude) <= 180
  )
}

function getRegionBounds(
  query: string
): L.LatLngBounds | null {
  if (query.includes('神奈川')) {
    // 神奈川県のおおよその範囲
    // 行政境界の正確なデータではない
    return L.latLngBounds(
      [35.12, 138.90],
      [35.69, 139.85]
    )
  }

  return null
}

function applyMapView(
  map: L.Map,
  fields: MappableField[],
  regionQuery: string
) {
  const region = getRegionBounds(regionQuery)

  if (region) {
    map.fitBounds(region, {
      padding: [20, 20],
      animate: false,
    })
    return
  }

  if (fields.length === 0) {
    map.setView([36.2, 138.2], 6, {
      animate: false,
    })
    return
  }

  if (fields.length === 1) {
    map.setView(
      [fields[0].latitude, fields[0].longitude],
      10,
      { animate: false }
    )
    return
  }

  const bounds = L.latLngBounds(
    fields.map((field) => [
      field.latitude,
      field.longitude,
    ])
  )

  map.fitBounds(bounds, {
    padding: [35, 35],
    maxZoom: 12,
    animate: false,
  })
}

function FitMarkers({
  fields,
  regionQuery,
}: {
  fields: MappableField[]
  regionQuery: string
}) {
  const map = useMap()

  const signature = fields
    .map(
      (field) =>
        `${field.id}:${field.latitude}:${field.longitude}`
    )
    .join('|')

  useEffect(() => {
    map.invalidateSize()
    applyMapView(map, fields, regionQuery)

    // 座標と検索地域が変わった場合だけ表示範囲を更新
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [map, signature, regionQuery])

  return null
}

function ResetMapView({
  fields,
  regionQuery,
}: {
  fields: MappableField[]
  regionQuery: string
}) {
  const map = useMap()

  const reset = () => {
    map.invalidateSize()
    applyMapView(map, fields, regionQuery)
  }

  return (
    <button
      type="button"
      className="field_map_reset"
      onClick={reset}
      aria-label="地図の表示範囲を戻す"
    >
      表示範囲を戻す
    </button>
  )
}

function FieldMapCanvas({
  fields,
  regionQuery = '',
}: FieldMapProps) {
  const mappedFields = useMemo(
    () => fields.filter(hasCoordinates),
    [fields]
  )

  return (
    <section className="field_map_section">
      <div className="field_map_header">
        <div>
          <p className="field_map_eyebrow">
            EXPLORE THE MAP
          </p>
          <h2>FIELD MAP.</h2>
        </div>

        <span className="field_map_count">
          {mappedFields.length} LOCATIONS
        </span>
      </div>

      <div className="field_map_wrapper">
        <MapContainer
          center={[36.2, 138.2]}
          zoom={6}
          scrollWheelZoom={false}
          className="field_map"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
            updateWhenIdle
            keepBuffer={1}
          />

          <FitMarkers
            fields={mappedFields}
            regionQuery={regionQuery}
          />

          <ResetMapView
            fields={mappedFields}
            regionQuery={regionQuery}
          />

          {mappedFields.map((field) => (
            <Marker
              key={field.id}
              position={[
                field.latitude,
                field.longitude,
              ]}
              icon={markerIcon}
            >
              <Popup>
                <div className="field_map_popup">
                  <strong>{field.name}</strong>

                  <p>
                    {field.prefecture} / {field.city}
                  </p>

                  <Link to={`/fields/${field.id}`}>
                    VIEW DETAILS →
                  </Link>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>

        {mappedFields.length === 0 && (
          <div className="field_map_empty">
            <strong>位置情報を準備中</strong>
            <p>
              この検索条件では、座標登録済みの
              フィールドがありません。
            </p>
          </div>
        )}
      </div>

      <p className="field_map_note">
        座標を確認できたフィールドのみ表示しています。
        地図上の位置と実際の入口は異なる場合があります。
      </p>
    </section>
  )
}

export default FieldMapCanvas
