import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Onboarding from './pages/Onboarding'
import PortfolioResult from './pages/PortfolioResult'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Onboarding />} />
        <Route path="/onboarding" element={<Onboarding />} />
        <Route path="/result" element={<PortfolioResult />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App

