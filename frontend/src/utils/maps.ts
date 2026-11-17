
import type { Field } from '../types/field'

export function getGoogleMapsUrl(field: Field): string {
  const hasDetailedAddress =
    !field.address.includes('詳細住所未確認')

  const query = hasDetailedAddress
    ? `${field.name}, ${field.address}`
    : `${field.name}, ${field.prefecture}${field.city}`

  return (
    'https://www.google.com/maps/search/?api=1&query=' +
    encodeURIComponent(query)
  )
}
