
/**
 * FIELD//BASE 柔軟なフィールド検索
 *
 * 対応:
 * - 全角・半角
 * - 英字の大文字・小文字
 * - ひらがな・カタカナ
 * - 都道府県名の別表記
 * - ローマ字の表記揺れ
 * - 複数キーワード（AND検索）
 */

const prefectureAliases: Record<string, string[]> = {
  北海道: ['ほっかいどう', 'hokkaido', 'hokkaidou'],
  青森県: ['あおもり', 'aomori'],
  岩手県: ['いわて', 'iwate'],
  宮城県: ['みやぎ', 'miyagi'],
  秋田県: ['あきた', 'akita'],
  山形県: ['やまがた', 'yamagata'],
  福島県: ['ふくしま', 'fukushima'],
  茨城県: ['いばらき', 'ibaraki', 'ibaragi'],
  栃木県: ['とちぎ', 'tochigi', 'totigi'],
  群馬県: ['ぐんま', 'gunma', 'gumma'],
  埼玉県: ['さいたま', 'saitama'],
  千葉県: ['ちば', 'chiba', 'tiba'],
  東京都: ['とうきょう', 'tokyo', 'toukyou', 'tokyou'],
  神奈川県: ['かながわ', 'kanagawa'],
  新潟県: ['にいがた', 'niigata'],
  富山県: ['とやま', 'toyama'],
  石川県: ['いしかわ', 'ishikawa', 'isikawa'],
  福井県: ['ふくい', 'fukui'],
  山梨県: ['やまなし', 'yamanashi', 'yamanasi'],
  長野県: ['ながの', 'nagano'],
  岐阜県: ['ぎふ', 'gifu'],
  静岡県: ['しずおか', 'shizuoka', 'sizuoka'],
  愛知県: ['あいち', 'aichi', 'aiti'],
  三重県: ['みえ', 'mie'],
  滋賀県: ['しが', 'shiga', 'siga'],
  京都府: ['きょうと', 'kyoto', 'kyouto'],
  大阪府: ['おおさか', 'osaka', 'oosaka'],
  兵庫県: ['ひょうご', 'hyogo', 'hyougo'],
  奈良県: ['なら', 'nara'],
  和歌山県: ['わかやま', 'wakayama'],
  鳥取県: ['とっとり', 'tottori'],
  島根県: ['しまね', 'shimane', 'simane'],
  岡山県: ['おかやま', 'okayama'],
  広島県: ['ひろしま', 'hiroshima', 'hirosima'],
  山口県: ['やまぐち', 'yamaguchi', 'yamaguti'],
  徳島県: ['とくしま', 'tokushima', 'tokusima'],
  香川県: ['かがわ', 'kagawa'],
  愛媛県: ['えひめ', 'ehime'],
  高知県: ['こうち', 'kochi', 'kouchi', 'kouti'],
  福岡県: ['ふくおか', 'fukuoka'],
  佐賀県: ['さが', 'saga'],
  長崎県: ['ながさき', 'nagasaki'],
  熊本県: ['くまもと', 'kumamoto'],
  大分県: ['おおいた', 'oita', 'ooita'],
  宮崎県: ['みやざき', 'miyazaki'],
  鹿児島県: ['かごしま', 'kagoshima', 'kagosima'],
  沖縄県: ['おきなわ', 'okinawa'],
}

export function normalizeSearchText(value: string): string {
  return value
    .normalize('NFKC')
    .toLowerCase()
    .replace(/[ァ-ヶ]/g, (character) =>
      String.fromCharCode(character.charCodeAt(0) - 0x60)
    )
    .replace(/\s+/g, '')
}

function getPrefectureKeywords(prefecture: string): string[] {
  const normalized = normalizeSearchText(prefecture)

  const entry = Object.entries(prefectureAliases).find(
    ([name]) =>
      normalizeSearchText(name) === normalized ||
      normalizeSearchText(
        name.replace(/[都道府県]$/, '')
      ) === normalized
  )

  if (!entry) {
    return [prefecture]
  }

  const [name, aliases] = entry

  return [
    name,
    name.replace(/[都道府県]$/, ''),
    ...aliases,
  ]
}

export type SearchableField = {
  name?: string | null
  prefecture?: string | null
  city?: string | null
  address?: string | null
  description?: string | null
  indoor?: boolean | null
  rental?: boolean | null
}

export function matchesFieldSearch(
  field: SearchableField,
  query: string
): boolean {
  const words = query
    .normalize('NFKC')
    .trim()
    .split(/\s+/)
    .filter(Boolean)

  if (words.length === 0) {
    return true
  }

  const prefectureKeywords = getPrefectureKeywords(
    field.prefecture ?? ''
  )

  const searchText = normalizeSearchText(
    [
      field.name,
      field.prefecture,
      field.city,
      field.address,
      field.description,
      ...prefectureKeywords,
      field.indoor
        ? '屋内 インドア indoor'
        : '屋外 アウトドア outdoor',
      field.rental ? 'レンタル rental' : '',
    ]
      .filter(Boolean)
      .join(' ')
  )

  return words.every((word) =>
    searchText.includes(normalizeSearchText(word))
  )
}

/**
 * 検索語から都道府県を判定する。
 *
 * 例:
 * - "tiba" -> "千葉県"
 * - "totigi" -> "栃木県"
 * - "かながわ" -> "神奈川県"
 * - "千葉 サバゲー" -> "千葉県"
 *
 * 複数の都道府県が含まれる場合は
 * 地図の地域を一意に特定しない。
 */
export function resolveRegionQuery(query: string): string {
  const normalized = normalizeSearchText(query)

  if (!normalized) {
    return ''
  }

  const matches: string[] = []

  for (const prefecture of Object.keys(prefectureAliases)) {
    const candidates = getPrefectureKeywords(prefecture)

    const matched = candidates.some((candidate) => {
      const keyword = normalizeSearchText(candidate)

      return keyword.length >= 2 &&
        normalized.includes(keyword)
    })

    if (matched) {
      matches.push(prefecture)
    }
  }

  if (matches.length === 1) {
    return matches[0]
  }

  return query
}
