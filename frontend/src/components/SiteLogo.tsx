import { Link } from 'react-router-dom'
import './SiteLogo.css'

type SiteLogoProps = {
  showText?: boolean
}

function SiteLogo({ showText = true }: SiteLogoProps) {
  return (
    <Link to="/" className="fb_site_logo" aria-label="FIELD//BASE トップページ">
      <img
        src="/fieldbase-mark.png"
        alt=""
        className="fb_site_logo_image"
      />

      {showText && (
        <span className="fb_site_logo_text">
          FIELD<span className="fb_site_logo_slashes">//</span>BASE
        </span>
      )}
    </Link>
  )
}

export default SiteLogo