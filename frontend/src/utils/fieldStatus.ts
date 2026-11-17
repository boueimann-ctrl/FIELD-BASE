
import type { Field } from '../types/field'

export type FieldStatus = {
  hasAddress: boolean
  hasCoordinates: boolean
  hasPrice: boolean
  hasRentalInfo: boolean
  hasWebsite: boolean
  hasImage: boolean
  isVerified: boolean
  completedCount: number
  totalCount: number
}

export function getFieldStatus(
  field: Field,
  imageUrl?: string
): FieldStatus {
  const hasAddress =
    field.address.trim().length > 0 &&
    !field.address.includes('詳細住所未確認')

  const hasCoordinates =
    typeof field.latitude === 'number' &&
    typeof field.longitude === 'number' &&
    Number.isFinite(field.latitude) &&
    Number.isFinite(field.longitude) &&
    Math.abs(field.latitude) <= 90 &&
    Math.abs(field.longitude) <= 180

  const hasPrice = field.price !== null

  const hasRentalInfo = field.rental !== null

  const hasWebsite =
    field.website.startsWith('https://') ||
    field.website.startsWith('http://')

  const hasImage = Boolean(imageUrl ?? field.imageUrl)

  const isVerified = Boolean(field.verifiedAt)

  const checks = [
    hasAddress,
    hasCoordinates,
    hasPrice,
    hasRentalInfo,
    hasWebsite,
    hasImage,
    isVerified,
  ]

  return {
    hasAddress,
    hasCoordinates,
    hasPrice,
    hasRentalInfo,
    hasWebsite,
    hasImage,
    isVerified,
    completedCount: checks.filter(Boolean).length,
    totalCount: checks.length,
  }
}
