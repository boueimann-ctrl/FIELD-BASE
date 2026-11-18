
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

const verifiedFields: Record<string, VerifiedFieldData> = {
  'blkfox-fussa': {
    verifiedAt: '2026-11-19',
    sourceUrl: 'https://blkfox.jp/fussa/',
    website: 'https://blkfox.jp/fussa/',
    address: '東京都福生市福生768 マルフジビルB1',
    rental: true,
    beginnerFriendly: true,
  },

  'blkfox-atsugi': {
    verifiedAt: '2026-11-19',
    sourceUrl: 'https://blkfox.jp/honatsugi/',
    website: 'https://blkfox.jp/honatsugi/',
    address: '神奈川県厚木市中町2-4-13 本厚木駅前ビル4F',
    rental: true,
    beginnerFriendly: true,
  },

  'asobiba-ikebukuro': {
    verifiedAt: '2026-11-17',
    sourceUrl: 'https://asobiba-tokyo.com/fields/ikebukuro',
    website: 'https://asobiba-tokyo.com/fields/ikebukuro',
    address: '東京都豊島区南池袋3-9-5 サトミビル地下2F',
    rental: true,
    beginnerFriendly: true,
  },

  'asobiba-shinkiba': {
    verifiedAt: '2026-11-18',
    sourceUrl: 'https://asobiba-tokyo.com/fields/shinkiba',
    website: 'https://asobiba-tokyo.com/fields/shinkiba',
    address: '東京都江東区新木場1-2-17',
    rental: true,
    beginnerFriendly: true,
  },

  'bravepoint-daiba': {
    verifiedAt: '2026-11-17',
    sourceUrl: 'https://odaiba.brave-point.jp/access/',
    website: 'https://odaiba.brave-point.jp/',
    address:
      '東京都港区台場1-6-1 デックス東京ビーチ アイランドモール5F',
    rental: true,
    beginnerFriendly: true,
  },

  'desert-union': {
    website: 'https://sites.google.com/view/desert-union/home',
    sourceUrl: 'https://sites.google.com/view/desert-union/home',
  },

  'tenkoo': {
    verifiedAt: '2026-11-18',
    website: 'https://tenkoo.tokyo/',
    sourceUrl: 'https://www.tenkoo.tokyo/access.html',
    rental: true,
    beginnerFriendly: true,
  },

  'ops': {
    verifiedAt: '2026-11-18',
    website: 'https://svg-ops.jp/',
    sourceUrl: 'https://svg-ops.jp/',
  },

  'tokyo-sabage-park': {
    verifiedAt: '2026-11-18',
    website: 'https://www.tokyosabagepark.jp/',
    sourceUrl: 'https://www.tokyosabagepark.jp/',
  },

  'cimax': {
    verifiedAt: '2026-11-18',
    website: 'https://www.cimax.jp/',
    sourceUrl: 'https://www.cimax.jp/',
    rental: true,
  },

  'sabage-paradise': {
    verifiedAt: '2026-11-18',
    website: 'https://survivalgameparadise.com/',
    sourceUrl: 'https://survivalgameparadise.com/',
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
