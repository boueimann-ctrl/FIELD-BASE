
import type { Field } from '../types/field'

function getFieldQuery(field: Field): string {
  const hasAddress =
    field.address.trim() !== '' &&
    !field.address.includes('詳細住所未確認')

  return hasAddress
    ? `${field.name} ${field.address}`
    : `${field.name} ${field.prefecture}${field.city}`
}

export function getGoogleMapsUrl(field: Field): string {
  return (
    'https://www.google.com/maps/search/?api=1&query=' +
    encodeURIComponent(getFieldQuery(field))
  )
}

export function getGoogleMapsDirectionsUrl(
  field: Field
): string {
  const hasCoordinates =
    typeof field.latitude === 'number' &&
    typeof field.longitude === 'number' &&
    Number.isFinite(field.latitude) &&
    Number.isFinite(field.longitude) &&
    Math.abs(field.latitude) <= 90 &&
    Math.abs(field.longitude) <= 180

  const destination = hasCoordinates
    ? `${field.latitude},${field.longitude}`
    : getFieldQuery(field)

  const params = new URLSearchParams({
    api: '1',
    destination,
  })

  return `https://www.google.com/maps/dir/?${params.toString()}`
}
