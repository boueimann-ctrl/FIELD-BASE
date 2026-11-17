
import type { Field } from '../types/field'

export const fields: Field[] = [
  {
    id: 'demo-001',
    name: 'DEMO FIELD TOKYO',
    prefecture: '東京都',
    city: '八王子市',
    address: 'デモ用データ',
    price: 3500,
    indoor: false,
    rental: true,
    beginnerFriendly: true,
    description: '初心者でも参加しやすい屋外フィールド。',
    website: '',
  },
  {
    id: 'demo-002',
    name: 'DEMO FIELD KANAGAWA',
    prefecture: '神奈川県',
    city: '横浜市',
    address: 'デモ用データ',
    price: 4000,
    indoor: true,
    rental: true,
    beginnerFriendly: true,
    description: '屋内で天候を気にせず楽しめるフィールド。',
    website: '',
  },
  {
    id: 'demo-003',
    name: 'DEMO FIELD CHIBA',
    prefecture: '千葉県',
    city: '千葉市',
    address: 'デモ用データ',
    price: 3000,
    indoor: false,
    rental: false,
    beginnerFriendly: false,
    description: '経験者向けの屋外フィールド。',
    website: '',
  },
]
