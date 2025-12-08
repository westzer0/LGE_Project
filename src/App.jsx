import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Onboarding from './pages/Onboarding'
import PortfolioResult from './pages/PortfolioResult'
import Section1 from './pages/Section1'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Section1 />} />
        <Route path="/onboarding" element={<Onboarding />} />
        <Route path="/result" element={<PortfolioResult />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App

