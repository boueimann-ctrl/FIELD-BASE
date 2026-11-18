
import type { Field } from '../types/field'
import verifiedLocationData from './generated/verifiedFieldLocations.json'

export type FieldCoordinates = {
  latitude: number
  longitude: number
}

const manuallyVerifiedLocations: Record<
  string,
  FieldCoordinates
> = {
  // BLKFOX 福生店
  'blkfox-fussa': {
    latitude: 35.742206302235275,
    longitude: 139.32734459630748,
  },

  // BLKFOX 本厚木店
  'blkfox-atsugi': {
    latitude: 35.44064690038472,
    longitude: 139.3653544962937,
  },

  // 東京サバゲパーク
  'tokyo-sabage-park': {
    latitude: 35.79075701160595,
    longitude: 140.1502336098031,
  },

  // yaNex
  'yanex': {
    latitude: 36.00587137248421,
    longitude: 139.8380606758022,
  },
}

const importedVerifiedLocations: Record<
  string,
  FieldCoordinates
> = verifiedLocationData

export const fieldLocations: Record<
  string,
  FieldCoordinates
> = {
  ...importedVerifiedLocations,
  ...manuallyVerifiedLocations,
}

function hasValidCoordinates(
  coordinates: FieldCoordinates
): boolean {
  return (
    Number.isFinite(coordinates.latitude) &&
    Number.isFinite(coordinates.longitude) &&
    coordinates.latitude >= -90 &&
    coordinates.latitude <= 90 &&
    coordinates.longitude >= -180 &&
    coordinates.longitude <= 180
  )
}

export function attachFieldLocations(
  sourceFields: Field[]
): Field[] {
  return sourceFields.map((field) => {
    const coordinates = fieldLocations[field.id]

    if (!coordinates) {
      return field
    }

    if (!hasValidCoordinates(coordinates)) {
      return field
    }

    return {
      ...field,
      latitude: coordinates.latitude,
      longitude: coordinates.longitude,
    }
  })
}
