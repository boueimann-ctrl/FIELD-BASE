import {
  BrowserRouter,
  Routes,
  Route,
} from 'react-router-dom'

import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import FieldsPage from './pages/FieldsPage'
import FieldDetailPage from './pages/FieldDetailPage'
import ContactPage from './pages/ContactPage'

import MobileBottomNav from './components/MobileBottomNav'
import ScrollToTop from './components/ScrollToTop'

function App() {
  return (
    <BrowserRouter>
      <ScrollToTop />

      <Routes>
        <Route
          path="/"
          element={<LandingPage />}
        />

        <Route
          path="/login"
          element={<LoginPage />}
        />

        <Route
          path="/fields"
          element={<FieldsPage />}
        />

        <Route
          path="/fields/:id"
          element={<FieldDetailPage />}
        />

        <Route
          path="/contact"
          element={<ContactPage />}
        />
      </Routes>

      <MobileBottomNav />
    </BrowserRouter>
  )
}

export default App