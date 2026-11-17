
import type { Field } from '../types/field'

export type FieldCoordinates = {
  latitude: number
  longitude: number
}

export const fieldLocations: Record<
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
}

export function attachFieldLocations(
  sourceFields: Field[]
): Field[] {
  return sourceFields.map((field) => {
    const coordinates = fieldLocations[field.id]

    if (!coordinates) {
      return field
    }

    return {
      ...field,
      latitude: coordinates.latitude,
      longitude: coordinates.longitude,
    }
  })
}
