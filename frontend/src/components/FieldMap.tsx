
import {
  lazy,
  Suspense,
  useEffect,
  useRef,
  useState,
} from 'react'

import type { Field } from '../types/field'

import './FieldMap.css'

const FieldMapCanvas = lazy(
  () => import('./FieldMapCanvas')
)

type FieldMapProps = {
  fields: Field[]
}

function FieldMap({ fields }: FieldMapProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [shouldLoad, setShouldLoad] = useState(
    () =>
      typeof window !== 'undefined' &&
      !('IntersectionObserver' in window)
  )

  useEffect(() => {
    if (shouldLoad) return

    const element = containerRef.current

    if (!element) return

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setShouldLoad(true)
          observer.disconnect()
        }
      },
      {
        rootMargin: '150px 0px',
        threshold: 0,
      }
    )

    observer.observe(element)

    return () => observer.disconnect()
  }, [shouldLoad])

  return (
    <div ref={containerRef}>
      {shouldLoad ? (
        <Suspense
          fallback={
            <div
              className="field_map_loading"
              role="status"
            >
              地図を読み込んでいます...
            </div>
          }
        >
          <FieldMapCanvas fields={fields} />
        </Suspense>
      ) : (
        <div
          className="field_map_loading"
          role="status"
        >
          地図を準備中...
        </div>
      )}
    </div>
  )
}

export default FieldMap
