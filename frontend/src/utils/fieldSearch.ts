
/**
 * FIELD//BASE 柔軟なフィールド検索
 *
 * 対応:
 * - 全角・半角
 * - 英字の大文字・小文字
 * - ひらがな・カタカナ
 * - 都道府県名の別表記
 * - 複数キーワード（AND検索）
 */

const prefectureAliases: Record<string, string[]> = {
  北海道: ['ほっかいどう', 'hokkaido'],
  青森県: ['あおもり', 'aomori'],
  岩手県: ['いわて', 'iwate'],
  宮城県: ['みやぎ', 'miyagi'],
  秋田県: ['あきた', 'akita'],
  山形県: ['やまがた', 'yamagata'],
  福島県: ['ふくしま', 'fukushima'],
  茨城県: ['いばらき', 'ibaraki'],
  栃木県: ['とちぎ', 'tochigi'],
  群馬県: ['ぐんま', 'gunma'],
  埼玉県: ['さいたま', 'saitama'],
  千葉県: ['ちば', 'chiba'],
  東京都: ['とうきょう', 'tokyo'],
  神奈川県: ['かながわ', 'kanagawa'],
  新潟県: ['にいがた', 'niigata'],
  富山県: ['とやま', 'toyama'],
  石川県: ['いしかわ', 'ishikawa'],
  福井県: ['ふくい', 'fukui'],
  山梨県: ['やまなし', 'yamanashi'],
  長野県: ['ながの', 'nagano'],
  岐阜県: ['ぎふ', 'gifu'],
  静岡県: ['しずおか', 'shizuoka'],
  愛知県: ['あいち', 'aichi'],
  三重県: ['みえ', 'mie'],
  滋賀県: ['しが', 'shiga'],
  京都府: ['きょうと', 'kyoto'],
  大阪府: ['おおさか', 'osaka'],
  兵庫県: ['ひょうご', 'hyogo'],
  奈良県: ['なら', 'nara'],
  和歌山県: ['わかやま', 'wakayama'],
  鳥取県: ['とっとり', 'tottori'],
  島根県: ['しまね', 'shimane'],
  岡山県: ['おかやま', 'okayama'],
  広島県: ['ひろしま', 'hiroshima'],
  山口県: ['やまぐち', 'yamaguchi'],
  徳島県: ['とくしま', 'tokushima'],
  香川県: ['かがわ', 'kagawa'],
  愛媛県: ['えひめ', 'ehime'],
  高知県: ['こうち', 'kochi'],
  福岡県: ['ふくおか', 'fukuoka'],
  佐賀県: ['さが', 'saga'],
  長崎県: ['ながさき', 'nagasaki'],
  熊本県: ['くまもと', 'kumamoto'],
  大分県: ['おおいた', 'oita'],
  宮崎県: ['みやざき', 'miyazaki'],
  鹿児島県: ['かごしま', 'kagoshima'],
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
      normalizeSearchText(name.replace(/[都道府県]$/, '')) === normalized
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
      field.indoor ? '屋内 インドア indoor' : '屋外 アウトドア outdoor',
      field.rental ? 'レンタル rental' : '',
    ]
      .filter(Boolean)
      .join(' ')
  )

  // すべての検索語を含む場合にヒット
  return words.every((word) =>
    searchText.includes(normalizeSearchText(word))
  )
}

/**
 * 検索語に含まれる都道府県の別表記を
 * 地図表示用の正式名称に変換する。
 */
export function resolveRegionQuery(query: string): string {
  const normalized = normalizeSearchText(query)

  for (const [prefecture, aliases] of Object.entries(
    prefectureAliases
  )) {
    const candidates = getPrefectureKeywords(prefecture)

    if (
      [...candidates, ...aliases].some((candidate) =>
        normalized.includes(normalizeSearchText(candidate))
      )
    ) {
      return prefecture
    }
  }

  return query
}
