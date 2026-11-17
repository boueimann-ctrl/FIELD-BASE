
import type { Field } from '../types/field'
import { getFieldImage } from '../data/fieldImages'
import { getFieldStatus } from '../utils/fieldStatus'
import './FieldStatus.css'

type FieldStatusProps = {
  field: Field
  variant?: 'compact' | 'full'
}

function FieldStatus({
  field,
  variant = 'compact',
}: FieldStatusProps) {
  const imageUrl = getFieldImage(field.id, field.imageUrl)
  const status = getFieldStatus(field, imageUrl)

  const items = [
    { label: '住所', ready: status.hasAddress },
    { label: '座標', ready: status.hasCoordinates },
    { label: '料金', ready: status.hasPrice },
    { label: 'レンタル', ready: status.hasRentalInfo },
    { label: '公式サイト', ready: status.hasWebsite },
    { label: '写真', ready: status.hasImage },
    { label: '情報確認日', ready: status.isVerified },
  ]

  const percentage = Math.round(
    (status.completedCount / status.totalCount) * 100
  )

  if (variant === 'compact') {
    return (
      <div className="fb_status_compact">
        <span>情報登録</span>
        <strong>
          {status.completedCount}/{status.totalCount}
        </strong>
        <div
          className="fb_status_track"
          role="progressbar"
          aria-label={`${field.name}の情報登録率`}
          aria-valuenow={status.completedCount}
          aria-valuemin={0}
          aria-valuemax={status.totalCount}
        >
          <div
            className="fb_status_fill"
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
    )
  }

  return (
    <section className="fb_status_full">
      <div className="fb_status_heading">
        <div>
          <p className="fb_status_eyebrow">
            INFORMATION STATUS
          </p>
          <h2>掲載情報の登録状況</h2>
        </div>
        <span>
          {status.completedCount}/{status.totalCount}
        </span>
      </div>

      <div
        className="fb_status_track"
        role="progressbar"
        aria-label={`${field.name}の情報登録率`}
        aria-valuenow={status.completedCount}
        aria-valuemin={0}
        aria-valuemax={status.totalCount}
      >
        <div
          className="fb_status_fill"
          style={{ width: `${percentage}%` }}
        />
      </div>

      <div className="fb_status_items">
        {items.map((item) => (
          <div className="fb_status_item" key={item.label}>
            <span
              className={
                item.ready
                  ? 'fb_status_indicator ready'
                  : 'fb_status_indicator'
              }
              aria-hidden="true"
            >
              {item.ready ? '✓' : '–'}
            </span>

            <span className="fb_status_item_label">
              {item.label}
            </span>

            <span className="fb_status_item_value">
              {item.ready ? '登録済み' : '未登録'}
            </span>
          </div>
        ))}
      </div>

      <p className="fb_status_disclaimer">
        登録状況は情報の有無を示すものであり、
        正確性や営業状況を保証するものではありません。
      </p>
    </section>
  )
}

export default FieldStatus
