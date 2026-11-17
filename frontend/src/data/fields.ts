
import type { Field } from '../types/field'

type FieldInput = {
  id: string
  name: string
  prefecture: string
  city: string
  address?: string
  indoor: boolean
  website?: string
  rental?: boolean | null
  beginnerFriendly?: boolean | null
  description?: string
  sourceUrl?: string
}

const DIRECTORY_SOURCE =
  'https://sightin.jp/field/map/?area=kanto'

const createField = (input: FieldInput): Field => ({
  id: input.id,
  name: input.name,
  prefecture: input.prefecture,
  city: input.city,
  address:
    input.address ??
    `${input.prefecture}${input.city}（詳細住所未確認）`,
  price: null,
  indoor: input.indoor,
  rental: input.rental ?? null,
  beginnerFriendly: input.beginnerFriendly ?? null,
  description:
    input.description ??
    `${input.prefecture}${input.city}にあるサバイバルゲームフィールド。料金や利用条件は施設へご確認ください。`,
  website: input.website ?? '',
  verifiedAt: null,
  sourceUrl: input.sourceUrl ?? DIRECTORY_SOURCE,
})

export const fields: Field[] = [
  // ========================================
  // 東京都
  // ========================================

  createField({
    id: 'blkfox-fussa',
    name: 'BLKFOX 福生店',
    prefecture: '東京都',
    city: '福生市',
    address: '東京都福生市福生768 マルフジビルB1',
    indoor: true,
    rental: true,
    website: 'https://blkfox.jp/',
    sourceUrl: 'https://blkfox.jp/',
  }),
  createField({
    id: 'asobiba-ikebukuro',
    name: 'ASOBIBA 池袋店',
    prefecture: '東京都',
    city: '豊島区',
    address: '東京都豊島区南池袋3-9-5 サトミビルB2F',
    indoor: true,
    rental: true,
    website: 'https://asobiba-tokyo.com/',
  }),
  createField({
    id: 'asobiba-shinkiba',
    name: 'ASOBIBA 新木場店',
    prefecture: '東京都',
    city: '江東区',
    address: '東京都江東区新木場1-2-17',
    indoor: true,
    rental: true,
    website: 'https://asobiba-tokyo.com/',
  }),
  createField({
    id: 'bravepoint-daiba',
    name: 'Brave Point 台場店',
    prefecture: '東京都',
    city: '港区',
    address: '東京都港区台場1-6-1 デックス東京ビーチ5F',
    indoor: true,
    website: 'https://www.brave-point.jp/',
  }),
  createField({
    id: 'tenkoo',
    name: 'TENKOO',
    prefecture: '東京都',
    city: '八王子市',
    address: '東京都八王子市高月町2205',
    indoor: false,
  }),
  createField({
    id: 'ops',
    name: 'OPS',
    prefecture: '東京都',
    city: '稲城市',
    address: '東京都稲城市坂浜734',
    indoor: false,
  }),
  createField({
    id: 'volcano',
    name: 'Volcano',
    prefecture: '東京都',
    city: '八王子市',
    address: '東京都八王子市戸吹町618-1',
    indoor: false,
  }),
  createField({
    id: 'ibf9',
    name: 'IBF9',
    prefecture: '東京都',
    city: '八王子市',
    address: '東京都八王子市下恩方町2938',
    indoor: true,
  }),
  createField({
    id: 'ramram',
    name: 'ラムラム',
    prefecture: '東京都',
    city: '葛飾区',
    address: '東京都葛飾区東四つ木2-9-7',
    indoor: true,
  }),

  // ========================================
  // 神奈川県
  // ========================================

  createField({
    id: 'blkfox-atsugi',
    name: 'BLKFOX 本厚木店',
    prefecture: '神奈川県',
    city: '厚木市',
    indoor: true,
    sourceUrl: DIRECTORY_SOURCE,
  }),
  createField({
    id: 'minna-no-mori',
    name: 'みんなの森',
    prefecture: '神奈川県',
    city: '厚木市',
    address: '神奈川県厚木市上荻野2781',
    indoor: false,
  }),
  createField({
    id: 'area41',
    name: 'AREA41 YOKOHAMA',
    prefecture: '神奈川県',
    city: '横浜市都筑区',
    indoor: true,
  }),
  createField({
    id: 'attacker',
    name: 'ATTACKER',
    prefecture: '神奈川県',
    city: '横浜市港北区',
    address: '神奈川県横浜市港北区新吉田町6061',
    indoor: false,
  }),
  createField({
    id: 'phantom-avenue',
    name: 'PHANTOM AVENUE',
    prefecture: '神奈川県',
    city: '相模原市緑区',
    indoor: false,
  }),
  createField({
    id: 'garden-z',
    name: 'ガーデンZ',
    prefecture: '神奈川県',
    city: '逗子市',
    indoor: false,
  }),
  createField({
    id: 'shonan-tosca',
    name: '湘南トスカフィールド',
    prefecture: '神奈川県',
    city: '平塚市',
    indoor: false,
  }),

  // ========================================
  // 千葉県
  // ========================================

  createField({
    id: 'tokyo-sabage-park',
    name: '東京サバゲパーク',
    prefecture: '千葉県',
    city: '印西市',
    address: '千葉県印西市草深字仲ノ側258番1他',
    indoor: false,
  }),
  createField({
    id: 'union-base',
    name: 'UNION BASE',
    prefecture: '千葉県',
    city: '印西市',
    address: '千葉県印西市平賀2858',
    indoor: false,
    rental: true,
  }),
  createField({
    id: 'desert-union',
    name: 'デザートユニオン',
    prefecture: '千葉県',
    city: '印西市',
    address: '千葉県印西市平賀2853',
    indoor: false,
    website: 'https://desert-union.jp/',
  }),
  createField({
    id: 'forest-union',
    name: 'フォレストユニオン',
    prefecture: '千葉県',
    city: '印西市',
    indoor: false,
  }),
  createField({
    id: 'met-union',
    name: 'METユニオン',
    prefecture: '千葉県',
    city: '印西市',
    indoor: false,
  }),
  createField({
    id: 'union-stadium',
    name: 'UNION STADIUM',
    prefecture: '千葉県',
    city: '印西市',
    indoor: false,
  }),
  createField({
    id: 'headshot',
    name: 'HEADSHOT',
    prefecture: '千葉県',
    city: '印西市',
    indoor: false,
  }),
  createField({
    id: 'little-headshot',
    name: 'リトルヘッドショット',
    prefecture: '千葉県',
    city: '印西市',
    indoor: false,
  }),
  createField({
    id: 'no9',
    name: 'NO.9',
    prefecture: '千葉県',
    city: '印西市',
    indoor: false,
  }),
  createField({
    id: 'savas',
    name: 'SAVAS',
    prefecture: '千葉県',
    city: '印西市',
    indoor: false,
  }),
  createField({
    id: 'cimax',
    name: 'CIMAX',
    prefecture: '千葉県',
    city: '印西市',
    address: '千葉県印西市師戸2300',
    indoor: false,
  }),
  createField({
    id: 'beam',
    name: 'BEAM',
    prefecture: '千葉県',
    city: '印西市',
    indoor: false,
  }),
  createField({
    id: 'war-zone',
    name: 'WAR ZONE Semper Fi',
    prefecture: '千葉県',
    city: '印西市',
    indoor: false,
  }),
  createField({
    id: 'yanex',
    name: 'yaNex',
    prefecture: '千葉県',
    city: '野田市',
    address: '千葉県野田市中里2655-1',
    indoor: false,
    rental: true,
    website: 'https://www.yanex.co/',
    sourceUrl: 'https://www.yanex.co/',
  }),
  createField({
    id: 'battle',
    name: 'BATTLE',
    prefecture: '千葉県',
    city: '千葉市花見川区',
    address: '千葉県千葉市花見川区柏井町478-1',
    indoor: false,
    website: 'https://www.battle-airsoft.com/',
    sourceUrl: 'https://www.battle-airsoft.com/',
  }),
  createField({
    id: 'bb-jungle',
    name: 'BB-JUNGLE',
    prefecture: '千葉県',
    city: '千葉市緑区',
    address: '千葉県千葉市緑区高田町1586',
    indoor: false,
    rental: true,
    website: 'https://pintail.wixsite.com/bbjungle',
    sourceUrl: 'https://pintail.wixsite.com/bbjungle',
  }),
  createField({
    id: 'seals',
    name: 'SEALs',
    prefecture: '千葉県',
    city: '千葉市若葉区',
    indoor: false,
  }),
  createField({
    id: 'athena',
    name: 'ATHENA',
    prefecture: '千葉県',
    city: '千葉市若葉区',
    indoor: false,
  }),
  createField({
    id: 'geronimo',
    name: 'GERONIMO',
    prefecture: '千葉県',
    city: '千葉市若葉区',
    indoor: false,
  }),
  createField({
    id: 'camp-devgru',
    name: 'CAMP DEVGRU',
    prefecture: '千葉県',
    city: '千葉市若葉区',
    indoor: false,
  }),
  createField({
    id: 'battle-city',
    name: 'バトルシティー',
    prefecture: '千葉県',
    city: '佐倉市',
    indoor: false,
  }),
  createField({
    id: 'paradox',
    name: 'PARADOX',
    prefecture: '千葉県',
    city: '君津市',
    indoor: false,
  }),
  createField({
    id: 'sabage-paradise',
    name: 'サバゲーパラダイス',
    prefecture: '千葉県',
    city: '山武市',
    address: '千葉県山武市大木470-1',
    indoor: false,
  }),
  createField({
    id: 'queen',
    name: 'Queen',
    prefecture: '千葉県',
    city: '富里市',
    indoor: false,
  }),
  createField({
    id: 'rockhill',
    name: 'RockHill',
    prefecture: '千葉県',
    city: '白井市',
    address: '千葉県白井市十余一60-15',
    indoor: false,
  }),
  createField({
    id: 'whitebase',
    name: 'ホワイトベース',
    prefecture: '千葉県',
    city: '白井市',
    indoor: false,
  }),
  createField({
    id: 'xx',
    name: 'XX（ダブルクロス）',
    prefecture: '千葉県',
    city: '市原市',
    indoor: false,
  }),
  createField({
    id: 'operation-freedom',
    name: 'オペレーションフリーダム',
    prefecture: '千葉県',
    city: '印旛郡酒々井町',
    indoor: false,
  }),

  // ========================================
  // 埼玉県
  // ========================================

  createField({
    id: 'sister',
    name: 'SISTER',
    prefecture: '埼玉県',
    city: 'さいたま市岩槻区',
    address: '埼玉県さいたま市岩槻区末田1849',
    indoor: false,
  }),
  createField({
    id: 'heads-kawagoe',
    name: 'H.E.A.D.S 川越',
    prefecture: '埼玉県',
    city: '川越市',
    indoor: false,
  }),
  createField({
    id: 'oasis',
    name: 'Oasis',
    prefecture: '埼玉県',
    city: '川越市',
    indoor: false,
  }),
  createField({
    id: 'assault2',
    name: 'アサルト2',
    prefecture: '埼玉県',
    city: '大里郡寄居町',
    address: '埼玉県大里郡寄居町牟礼1424',
    indoor: false,
  }),
  createField({
    id: 'assault3',
    name: 'アサルト3',
    prefecture: '埼玉県',
    city: '児玉郡美里町',
    address: '埼玉県児玉郡美里町猪俣666',
    indoor: false,
  }),
  createField({
    id: 'foxtrot',
    name: 'FOXTROT',
    prefecture: '埼玉県',
    city: '飯能市',
    address: '埼玉県飯能市原市場1104-1',
    indoor: true,
  }),
  createField({
    id: 'hq-reload',
    name: 'HQリロード',
    prefecture: '埼玉県',
    city: '日高市',
    address: '埼玉県日高市下大谷沢178-10',
    indoor: false,
  }),
  createField({
    id: 't-mout',
    name: 'T-MOUT',
    prefecture: '埼玉県',
    city: '東松山市',
    indoor: false,
  }),
  createField({
    id: 'kis-isf',
    name: 'KIS-ISF',
    prefecture: '埼玉県',
    city: '狭山市',
    address: '埼玉県狭山市北入曽694-23',
    indoor: true,
  }),
  createField({
    id: 'hills',
    name: "Hill's",
    prefecture: '埼玉県',
    city: '上尾市',
    indoor: false,
  }),

  // ========================================
  // 茨城県
  // ========================================

  createField({
    id: 'tsukuba-sabage-land',
    name: 'つくばサバゲーランド',
    prefecture: '茨城県',
    city: '龍ケ崎市',
    indoor: false,
  }),
  createField({
    id: 'survival-country',
    name: 'サバイバルカントリー',
    prefecture: '茨城県',
    city: '龍ケ崎市',
    indoor: false,
  }),
  createField({
    id: 'edge',
    name: 'EDGE',
    prefecture: '茨城県',
    city: '牛久市',
    indoor: false,
  }),
  createField({
    id: 'c-a-t',
    name: 'C.A.T.Facility',
    prefecture: '茨城県',
    city: '龍ケ崎市',
    indoor: false,
  }),
  createField({
    id: 'omisa',
    name: '小美鯖',
    prefecture: '茨城県',
    city: '小美玉市',
    indoor: false,
  }),
  createField({
    id: 'rise-secret-camp',
    name: 'Rise.Secret.Camp',
    prefecture: '茨城県',
    city: '潮来市',
    indoor: false,
  }),

  // ========================================
  // 栃木県
  // ========================================

  createField({
    id: 'f2plant',
    name: 'F2プラント',
    prefecture: '栃木県',
    city: '栃木市',
    indoor: true,
  }),
  createField({
    id: 'beforester',
    name: 'Beforester',
    prefecture: '栃木県',
    city: '下都賀郡壬生町',
    indoor: false,
  }),
  createField({
    id: 'head-ax',
    name: 'HEAD AX',
    prefecture: '栃木県',
    city: '那須烏山市',
    indoor: false,
  }),
  createField({
    id: 'sabage-park-nasu',
    name: 'サバゲパーク那須',
    prefecture: '栃木県',
    city: '那須郡那須町',
    indoor: false,
  }),

  // ========================================
  // 群馬県
  // ========================================

  createField({
    id: 'akagi357',
    name: 'AKAGI357',
    prefecture: '群馬県',
    city: '桐生市',
    indoor: false,
  }),
  createField({
    id: 'dragon-one',
    name: 'DRAGON-ONE',
    prefecture: '群馬県',
    city: '前橋市',
    indoor: false,
  }),
  createField({
    id: 'comrade-hills',
    name: 'COMRADE HILLS',
    prefecture: '群馬県',
    city: '桐生市',
    indoor: false,
  }),
  createField({
    id: 'gunfield-haruna',
    name: 'GUNFIELD HARUNA',
    prefecture: '群馬県',
    city: '高崎市',
    indoor: false,
  }),
]
