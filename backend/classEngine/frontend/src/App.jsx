import { Routes, Route } from 'react-router-dom'
import SearchPage from './components/SearchPage'
import ResultsPage from './components/ResultsPage'

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/results" element={<ResultsPage />} />
      </Routes>
    </div>
  )
}
