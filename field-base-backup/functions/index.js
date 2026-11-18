
const crypto = require('node:crypto')

const { onRequest } = require('firebase-functions/v2/https')
const { initializeApp } = require('firebase-admin/app')
const { getFirestore, FieldValue } = require('firebase-admin/firestore')

initializeApp()

const db = getFirestore()

const allowedOrigins = [
  'https://field-base-67118.web.app',
  'https://field-base-67118.firebaseapp.com',
]

const validTypes = new Set([
  'general',
  'correction',
  'owner',
  'feedback',
])

function isValidEmail(value) {
  return (
    typeof value === 'string' &&
    value.length <= 254 &&
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
  )
}

function isValidText(value, min, max) {
  return (
    typeof value === 'string' &&
    value.trim().length >= min &&
    value.trim().length <= max
  )
}

exports.submitContact = onRequest(
  {
    region: 'asia-northeast1',
    cors: allowedOrigins,
    maxInstances: 5,
    timeoutSeconds: 15,
    memory: '256MiB',
    invoker: 'public',
  },
  async (request, response) => {
    if (request.method !== 'POST') {
      response.status(405).json({
        error: 'POSTのみ利用できます。',
      })
      return
    }

    const body = request.body

    if (
      !body ||
      typeof body !== 'object' ||
      Array.isArray(body)
    ) {
      response.status(400).json({
        error: '送信データが不正です。',
      })
      return
    }

    const {
      type,
      name,
      email,
      fieldName,
      message,
      website,
    } = body

    // 画面に表示しない入力欄（簡易ボット対策）
    if (website) {
      response.status(200).json({ success: true })
      return
    }

    const requiresField =
      type === 'correction' || type === 'owner'

    if (
      !validTypes.has(type) ||
      !isValidText(name, 1, 100) ||
      !isValidEmail(email) ||
      !isValidText(message, 10, 3000) ||
      (requiresField && !isValidText(fieldName, 1, 150)) ||
      (!requiresField &&
        fieldName !== undefined &&
        fieldName !== '' &&
        !isValidText(fieldName, 1, 150))
    ) {
      response.status(400).json({
        error: '入力内容を確認してください。',
      })
      return
    }

    try {
      // IPアドレスをそのまま保存しないためハッシュ化
      const ip =
        request.ip ||
        request.socket.remoteAddress ||
        'unknown'

      const ipHash = crypto
        .createHash('sha256')
        .update(ip)
        .digest('hex')

      const now = Date.now()
      const windowMs = 60 * 60 * 1000
      const rateLimitRef = db
        .collection('contactRateLimits')
        .doc(ipHash)

      const messageRef = db
        .collection('contactMessages')
        .doc()

      const result = await db.runTransaction(
        async (transaction) => {
          const snapshot = await transaction.get(rateLimitRef)
          const previous = snapshot.data()

          const windowStart =
            typeof previous?.windowStart === 'number'
              ? previous.windowStart
              : 0

          const withinWindow =
            now - windowStart < windowMs

          const count = withinWindow
            ? Number(previous?.count || 0)
            : 0

          if (count >= 5) {
            return false
          }

          transaction.set(rateLimitRef, {
            windowStart: withinWindow ? windowStart : now,
            count: count + 1,
            updatedAt: FieldValue.serverTimestamp(),
          })

          transaction.create(messageRef, {
            type,
            name: name.trim(),
            email: email.trim(),
            fieldName:
              typeof fieldName === 'string'
                ? fieldName.trim()
                : '',
            message: message.trim(),
            status: 'unread',
            createdAt: FieldValue.serverTimestamp(),
          })

          return true
        }
      )

      if (!result) {
        response.status(429).json({
          error:
            '短時間に送信できる回数を超えました。時間をおいてお試しください。',
        })
        return
      }

      response.status(200).json({
        success: true,
      })
    } catch (error) {
      console.error('Contact submission failed:', error)

      response.status(500).json({
        error:
          '送信できませんでした。時間をおいて再度お試しください。',
      })
    }
  }
)
