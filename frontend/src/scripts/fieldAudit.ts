
import { fields } from '../data/fields'
import { fieldLocations } from '../data/fieldLocations'

const total = fields.length

const withCoordinates = fields.filter(
  (field) => fieldLocations[field.id] !== undefined
)

const withoutCoordinates = fields.filter(
  (field) => fieldLocations[field.id] === undefined
)

const withVerifiedDate = fields.filter(
  (field) => field.verifiedAt !== null
)

console.log('\nFIELD//BASE DATA AUDIT')
console.log('==========================')
console.log(`掲載候補: ${total}件`)
console.log(`座標登録済み: ${withCoordinates.length}件`)
console.log(`座標未登録: ${withoutCoordinates.length}件`)
console.log(`確認日登録済み: ${withVerifiedDate.length}件`)

console.log('\n座標未登録フィールド')
console.log('--------------------------')

withoutCoordinates.forEach((field, index) => {
  console.log(
    `${index + 1}. [${field.id}] ${field.name}`
  )
  console.log(`   ${field.prefecture} ${field.city}`)
  console.log(`   ${field.address}`)
})

console.log('\n==========================')
