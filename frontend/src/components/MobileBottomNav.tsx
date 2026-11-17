import { NavLink, useLocation } from 'react-router-dom'
import './MobileBottomNav.css'

type NavItem = {
  label: string
  to: string
  icon: 'home' | 'search' | 'map' | 'contact' | 'user'
}

const navItems: NavItem[] = [
  { label: 'ホーム', to: '/', icon: 'home' },
  { label: '検索', to: '/fields', icon: 'search' },
  { label: '地図', to: '/fields?view=map', icon: 'map' },
  { label: '連絡', to: '/contact', icon: 'contact' },
  { label: 'ログイン', to: '/login', icon: 'user' },
]

function NavIcon({ name }: { name: NavItem['icon'] }) {
  switch (name) {
    case 'home':
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="m3 10 9-7 9 7v10H3z" />
          <path d="M9 20v-7h6v7" />
        </svg>
      )

    case 'search':
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="10.5" cy="10.5" r="6.5" />
          <path d="m16 16 5 5" />
        </svg>
      )

    case 'map':
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="m3 5 6-2 6 2 6-2-6 2z" />
          <path d="M9 3v16M15 5v16" />
        </svg>
      )

    case 'contact':
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <rect x="3" y="5" width="18" height="14" rx="2" />
          <path d="m3 7 9 7 9-7" />
        </svg>
      )

    case 'user':
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="8" r="4" />
          <path d="M4 21c0-4 3.5-7 8-7s8 3 8 7" />
        </svg>
      )
  }
}

function MobileBottomNav() {
  const location = useLocation()

  return (
    <nav
      className="mobile_bottom_nav"
      aria-label="スマホ用メインナビゲーション"
    >
      {navItems.map((item) => {
        const isActive =
          item.icon === 'map'
            ? location.pathname === '/fields' &&
              new URLSearchParams(location.search).get('view') === 'map'
            : item.icon === 'search'
              ? location.pathname === '/fields' &&
                new URLSearchParams(location.search).get('view') !== 'map'
              : location.pathname === item.to

        return (
          <NavLink
            key={item.label}
            to={item.to}
            className={`mobile_bottom_nav_item ${
              isActive ? 'active' : ''
            }`}
            aria-current={isActive ? 'page' : undefined}
          >
            <NavIcon name={item.icon} />
            <span>{item.label}</span>
          </NavLink>
        )
      })}
    </nav>
  )
}

export default MobileBottomNav