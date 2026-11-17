
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import FieldsPage from './pages/FieldsPage'
import FieldDetailPage from './pages/FieldDetailPage'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/fields" element={<FieldsPage />} />
        <Route path="/fields/:id" element={<FieldDetailPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
