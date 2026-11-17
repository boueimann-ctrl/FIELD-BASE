import { fields } from '../src/data/fields'
import {
  attachFieldLocations,
} from '../src/data/fieldLocations'
import {
  attachFieldVerification,
} from '../src/data/fieldVerification'

const allFields = attachFieldLocations(
  attachFieldVerification(fields)
)

type AuditIssue = {
  id: string
  name: string
  issues: string[]
}

const issues: AuditIssue[] = []
const seenIds = new Set<string>()
const duplicateIds = new Set<string>()

const counts = {
  missingAddress: 0,
  missingCoordinates: 0,
  missingPrice: 0,
  missingRental: 0,
  missingBeginnerInfo: 0,
  missingWebsite: 0,
  missingVerification: 0,
  missingSource: 0,
  duplicateIds: 0,
}

const isValidUrl = (value: string): boolean => {
  try {
    const url = new URL(value)
    return url.protocol === 'https:' || url.protocol === 'http:'
  } catch {
    return false
  }
}

for (const field of allFields) {
  const fieldIssues: string[] = []

  if (seenIds.has(field.id)) {
    duplicateIds.add(field.id)
    fieldIssues.push('ID重複')
  }

  seenIds.add(field.id)

  if (
    !field.address.trim() ||
    field.address.includes('詳細住所未確認')
  ) {
    counts.missingAddress++
    fieldIssues.push('住所未確認')
  }

  if (
    typeof field.latitude !== 'number' ||
    typeof field.longitude !== 'number' ||
    !Number.isFinite(field.latitude) ||
    !Number.isFinite(field.longitude) ||
    Math.abs(field.latitude) > 90 ||
    Math.abs(field.longitude) > 180
  ) {
    counts.missingCoordinates++
    fieldIssues.push('位置情報未登録')
  }

  if (
    field.price === null ||
    !Number.isFinite(field.price) ||
    field.price < 0
  ) {
    counts.missingPrice++
    fieldIssues.push('料金未確認')
  }

  if (field.rental === null) {
    counts.missingRental++
    fieldIssues.push('レンタル未確認')
  }

  if (field.beginnerFriendly === null) {
    counts.missingBeginnerInfo++
    fieldIssues.push('初心者情報未確認')
  }

  if (!isValidUrl(field.website)) {
    counts.missingWebsite++
    fieldIssues.push('公式サイト未登録・URL不正')
  }

  if (
    !field.verifiedAt ||
    !/^\d{4}-\d{2}-\d{2}$/.test(field.verifiedAt)
  ) {
    counts.missingVerification++
    fieldIssues.push('情報確認日未登録')
  }

  if (!isValidUrl(field.sourceUrl ?? '')) {
    counts.missingSource++
    fieldIssues.push('参照元URL未登録・不正')
  }

  if (fieldIssues.length > 0) {
    issues.push({
      id: field.id,
      name: field.name,
      issues: fieldIssues,
    })
  }
}

counts.duplicateIds = duplicateIds.size

console.log('\n======================================')
console.log(' FIELD//BASE - DATA QUALITY AUDIT')
console.log('======================================\n')

console.log(`登録フィールド数: ${allFields.length}`)
console.log(`問題のあるフィールド数: ${issues.length}`)
console.log(
  `全項目を満たすフィールド数: ${
    allFields.length - issues.length
  }\n`
)

console.log('【項目別の不足件数】')
console.table([
  { 項目: '住所未確認', 件数: counts.missingAddress },
  { 項目: '位置情報未登録', 件数: counts.missingCoordinates },
  { 項目: '料金未確認', 件数: counts.missingPrice },
  { 項目: 'レンタル未確認', 件数: counts.missingRental },
  { 項目: '初心者情報未確認', 件数: counts.missingBeginnerInfo },
  { 項目: '公式サイト未登録・不正', 件数: counts.missingWebsite },
  { 項目: '情報確認日未登録', 件数: counts.missingVerification },
  { 項目: '参照元URL未登録・不正', 件数: counts.missingSource },
  { 項目: '重複IDの種類数', 件数: counts.duplicateIds },
])

console.log('\n【フィールド別の検査結果】\n')

for (const item of issues) {
  console.log(`${item.name} (${item.id})`)

  for (const issue of item.issues) {
    console.log(`  - ${issue}`)
  }

  console.log('')
}

if (issues.length === 0) {
  console.log('すべてのフィールドが検査条件を満たしています。')
} else {
  console.log(
    '※ 未確認項目は必ずしもデータの誤りを意味しません。'
  )
  console.log(
    '※ 公式サイトや施設の営業状況は別途確認が必要です。'
  )
}