
import type { Field } from '../types/field'

type VerifiedFieldData = Partial<
  Pick<
    Field,
    | 'verifiedAt'
    | 'sourceUrl'
    | 'website'
    | 'address'
    | 'rental'
    | 'beginnerFriendly'
  >
>

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
    verifiedAt: '2026-11-18',
    sourceUrl:
      'https://asobiba-tokyo.com/fields/shinkiba',
    website:
      'https://asobiba-tokyo.com/fields/shinkiba',
    address:
      '東京都江東区新木場1-2-17',
    rental: true,
    beginnerFriendly: true,
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

  // 公式サイトURLを確認済み。
  // 住所・料金・営業状況は別途確認する。
  'desert-union': {
    website:
      'https://sites.google.com/view/desert-union/home',
    sourceUrl:
      'https://sites.google.com/view/desert-union/home',
  },
}

export function attachFieldVerification(
  sourceFields: Field[]
): Field[] {
  return sourceFields.map((field) => {
    const verified = verifiedFields[field.id]

    if (!verified) {
      return field
    }

    return {
      ...field,
      ...verified,
    }
  })
}
