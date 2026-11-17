
export type Field = {
  id: string
  name: string
  prefecture: string
  city: string
  address: string

  price: number | null
  indoor: boolean
  rental: boolean | null
  beginnerFriendly: boolean | null

  description: string
  website: string
  imageUrl?: string

  verifiedAt: string | null
  sourceUrl: string

  latitude?: number
  longitude?: number
}
