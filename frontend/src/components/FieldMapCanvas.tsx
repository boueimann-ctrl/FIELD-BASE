
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

function FitMarkers({
  fields,
  signature,
}: {
  fields: MappableField[]
  signature: string
}) {
  const map = useMap()

  useEffect(() => {
    map.invalidateSize()

    if (fields.length === 0) {
      map.setView([35.7, 139.6], 9)
      return
    }

    if (fields.length === 1) {
      map.setView(
        [fields[0].latitude, fields[0].longitude],
        13
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
      maxZoom: 13,
      animate: false,
    })
    // signatureが変わったときだけ再計算する
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [signature, map])

  return null
}

function FieldMapCanvas({ fields }: FieldMapProps) {
  const mappedFields = useMemo(
    () => fields.filter(hasCoordinates),
    [fields]
  )

  const signature = mappedFields
    .map(
      (field) =>
        `${field.id}:${field.latitude}:${field.longitude}`
    )
    .join('|')

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
          center={[35.7, 139.6]}
          zoom={9}
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
            signature={signature}
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
