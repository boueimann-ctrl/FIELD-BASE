
export type Coordinates = {
  latitude: number
  longitude: number
}

const EARTH_RADIUS_KM = 6371

export function calculateDistance(
  from: Coordinates,
  to: Coordinates
): number {
  const toRadians = (degrees: number) =>
    (degrees * Math.PI) / 180

  const lat1 = toRadians(from.latitude)
  const lat2 = toRadians(to.latitude)

  const deltaLat = toRadians(
    to.latitude - from.latitude
  )
  const deltaLng = toRadians(
    to.longitude - from.longitude
  )

  const a =
    Math.sin(deltaLat / 2) ** 2 +
    Math.cos(lat1) *
      Math.cos(lat2) *
      Math.sin(deltaLng / 2) ** 2

  const c = 2 * Math.atan2(
    Math.sqrt(a),
    Math.sqrt(1 - a)
  )

  return EARTH_RADIUS_KM * c
}
