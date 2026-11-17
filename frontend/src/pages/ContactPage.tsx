
import { useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import './ContactPage.css'

type ContactType =
  | 'general'
  | 'correction'
  | 'owner'
  | 'feedback'

const GOOGLE_FORM_URL =
  'https://docs.google.com/forms/d/e/1FAIpQLSfB0-CN6Fn0sxSwK4nnWxZRQL-FNVk93E4nmX97EgkBDFiy2Q/viewform'

const CONTACT_TYPE_LABELS: Record<ContactType, string> = {
  general: '一般的なお問い合わせ',
  correction: 'フィールド情報の修正依頼',
  owner: 'フィールド運営者からのご連絡',
  feedback: 'サービスへのご意見・ご要望',
}

function ContactPage() {
  const [searchParams] = useSearchParams()

  const requestedType = searchParams.get('type')

  const initialType: ContactType =
    requestedType === 'correction' ||
    requestedType === 'owner' ||
    requestedType === 'feedback'
      ? requestedType
      : 'general'

  const [type, setType] = useState<ContactType>(initialType)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [fieldName, setFieldName] = useState(
    searchParams.get('field') ?? ''
  )
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const requiresFieldName =
    type === 'correction' || type === 'owner'

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')

    const trimmedName = name.trim()
    const trimmedEmail = email.trim()
    const trimmedFieldName = fieldName.trim()
    const trimmedMessage = message.trim()

    if (
      !trimmedName ||
      !trimmedEmail ||
      trimmedMessage.length < 10
    ) {
      setError('入力内容を確認してください。')
      return
    }

    if (requiresFieldName && !trimmedFieldName) {
      setError('対象フィールド名を入力してください。')
      return
    }

    const url = new URL(GOOGLE_FORM_URL)

    url.searchParams.set('usp', 'pp_url')

    url.searchParams.set(
      'entry.717781365',
      CONTACT_TYPE_LABELS[type]
    )

    url.searchParams.set(
      'entry.1571919918',
      trimmedName
    )

    url.searchParams.set(
      'entry.762212093',
      trimmedEmail
    )

    url.searchParams.set(
      'entry.2082996614',
      requiresFieldName ? trimmedFieldName : ''
    )

    url.searchParams.set(
      'entry.324048427',
      trimmedMessage
    )

    // Googleフォームで最終的な送信を行う。
    // この時点ではお問い合わせは送信されていない。
    window.location.assign(url.toString())
  }

  return (
    <main className="contact-page">
      <div className="contact-container">
        <Link to="/" className="contact-back">
          ← FIELD//BASE
        </Link>

        <div className="contact-heading">
          <span className="contact-eyebrow">
            SUPPORT / CONTACT
          </span>

          <h1>お問い合わせ</h1>

          <p>
            FIELD//BASEへのご質問、
            フィールド情報の修正依頼、
            サービスへのご意見をお寄せください。
          </p>
        </div>

        <form
          className="contact-form"
          onSubmit={handleSubmit}
        >
          <div className="contact-field">
            <label htmlFor="contact-type">
              お問い合わせ種別
              <span className="contact-required">
                必須
              </span>
            </label>

            <select
              id="contact-type"
              value={type}
              onChange={(event) =>
                setType(event.target.value as ContactType)
              }
              required
            >
              <option value="general">
                一般的なお問い合わせ
              </option>

              <option value="correction">
                フィールド情報の修正依頼
              </option>

              <option value="owner">
                フィールド運営者からのご連絡
              </option>

              <option value="feedback">
                サービスへのご意見・ご要望
              </option>
            </select>
          </div>

          <div className="contact-field">
            <label htmlFor="contact-name">
              お名前
              <span className="contact-required">
                必須
              </span>
            </label>

            <input
              id="contact-name"
              type="text"
              value={name}
              onChange={(event) =>
                setName(event.target.value)
              }
              placeholder="お名前"
              autoComplete="name"
              maxLength={100}
              required
            />
          </div>

          <div className="contact-field">
            <label htmlFor="contact-email">
              メールアドレス
              <span className="contact-required">
                必須
              </span>
            </label>

            <input
              id="contact-email"
              type="email"
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
              placeholder="example@email.com"
              autoComplete="email"
              maxLength={254}
              required
            />
          </div>

          {requiresFieldName && (
            <div className="contact-field">
              <label htmlFor="contact-field-name">
                対象フィールド名
                <span className="contact-required">
                  必須
                </span>
              </label>

              <input
                id="contact-field-name"
                type="text"
                value={fieldName}
                onChange={(event) =>
                  setFieldName(event.target.value)
                }
                placeholder="フィールド名を入力"
                maxLength={150}
                required
              />
            </div>
          )}

          <div className="contact-field">
            <label htmlFor="contact-message">
              お問い合わせ内容
              <span className="contact-required">
                必須
              </span>
            </label>

            <textarea
              id="contact-message"
              value={message}
              onChange={(event) =>
                setMessage(event.target.value)
              }
              placeholder="お問い合わせ内容をご入力ください。"
              rows={8}
              minLength={10}
              maxLength={3000}
              required
            />
          </div>

          {error && (
            <div
              className="contact-notice"
              role="alert"
              style={{ color: '#b42318' }}
            >
              {error}
            </div>
          )}

          <div className="contact-notice">
            <p>
              入力内容はGoogleフォームに引き継がれます。
              移動先で内容を確認し、
              Googleフォームの送信ボタンを押すと
              お問い合わせが完了します。
            </p>

            <p>
              お名前・メールアドレス・お問い合わせ内容は、
              回答を受け付けるためにGoogleフォームへ渡されます。
            </p>
          </div>

          <button
            type="submit"
            className="contact-submit"
          >
            Googleフォームで送信内容を確認する
          </button>
        </form>
      </div>
    </main>
  )
}

export default ContactPage
