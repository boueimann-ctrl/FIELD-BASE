
import { useState } from 'react'
import { getFieldImage } from '../data/fieldImages'
import './FieldImage.css'

type FieldImageProps = {
  fieldId: string
  fieldName: string
  imageUrl?: string
  variant?: 'card' | 'detail'
}

function FieldImage({
  fieldId,
  fieldName,
  imageUrl,
  variant = 'card',
}: FieldImageProps) {
  const image = getFieldImage(fieldId, imageUrl)

  const [failedImage, setFailedImage] = useState<
    string | null
  >(null)

  const showImage =
    Boolean(image) && image !== failedImage

  return (
    <div
      className={`fb_field_image fb_field_image_${variant}`}
    >
      {showImage && image ? (
        <img
          src={image}
          alt={`${fieldName}のフィールド写真`}
          loading="lazy"
          decoding="async"
          onError={() => setFailedImage(image)}
        />
      ) : (
        <div className="fb_field_image_placeholder">
          <span>FIELD//BASE</span>
          <small>IMAGE COMING SOON</small>
        </div>
      )}
    </div>
  )
}

export default FieldImage
