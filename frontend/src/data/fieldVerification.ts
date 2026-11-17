
import type { Field } from '../types/field'

type VerifiedFieldData = {
  verifiedAt: string
  sourceUrl: string
  website: string
  address: string
  rental?: boolean
  beginnerFriendly?: boolean
}

const verifiedFields: Record<
  string,
  VerifiedFieldData
> = {
  'asobiba-ikebukuro': {
    verifiedAt: '2026-11-17',
    sourceUrl:
      'https://asobiba-tokyo.com/fields/ikebukuro',
    website:
      'https://asobiba-tokyo.com/fields/ikebukuro',
    address:
      '東京都豊島区南池袋3-9-5 サトミビル地下2F',
    rental: true,
    beginnerFriendly: true,
  },

  'asobiba-shinkiba': {
    verifiedAt: '2026-11-17',
    sourceUrl:
      'https://asobiba-tokyo.com/fields',
    website:
      'https://asobiba-tokyo.com/fields',
    address:
      '東京都江東区新木場1-2-17',
  },

  'bravepoint-daiba': {
    verifiedAt: '2026-11-17',
    sourceUrl:
      'https://odaiba.brave-point.jp/access/',
    website:
      'https://odaiba.brave-point.jp/',
    address:
      '東京都港区台場1-6-1 デックス東京ビーチ アイランドモール5F',
    rental: true,
    beginnerFriendly: true,
  },
}

export function attachFieldVerification(
  sourceFields: Field[]
): Field[] {
  return sourceFields.map((field) => {
    const verified = verifiedFields[field.id]

    if (!verified) return field

    return {
      ...field,
      ...verified,
    }
  })
}
