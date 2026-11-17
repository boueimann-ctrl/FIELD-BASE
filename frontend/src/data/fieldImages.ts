
/**
 * FIELD//BASE - Field Images
 *
 * フィールドIDと画像パスの対応表。
 *
 * 画像は public/images/fields/ に配置する。
 * 画像未登録のフィールドはプレースホルダーを表示する。
 *
 * 使用する画像は自分で撮影した写真、
 * または掲載許可を得た写真に限定する。
 */

export const fieldImages: Record<string, string> = {
  // 画像を追加したら、以下の形式で登録する
  //
  // 'blkfox-fussa': '/images/fields/blkfox-fussa.webp',
  // 'tokyo-sabage-park': '/images/fields/tokyo-sabage-park.webp',
}

export function getFieldImage(
  fieldId: string,
  fallbackImage?: string
): string | undefined {
  return fieldImages[fieldId] ?? fallbackImage
}
