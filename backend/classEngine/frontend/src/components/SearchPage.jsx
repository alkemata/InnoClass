import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

const SDGS = ['No Poverty', 'Zero Hunger', /* … */]
const TARGETS = ['1.1 Eradicate poverty', '1.2 Social protection', /* … */]

export default function SearchPage() {
  const [mode, setMode] = useState('sdgs')
  const [sel, setSel] = useState([])
  const [keywords, setKeywords] = useState('')
  const navigate = useNavigate()

  const options = mode === 'sdgs' ? SDGS : TARGETS

  const onSearch = () => {
    navigate('/results', { state: { mode, sel, keywords } })
  }

  return (
    <div className="max-w-3xl mx-auto">
      {/* Logo bar */}
      <div className="bg-lime-400 h-10 flex items-center px-4">
        <span className="font-bold">InnoClass</span>
      </div>

      {/* Title */}
      <div className="p-6">
        <h1 className="text-xl font-semibold mb-6">SDG Search Engine for patents demo:</h1>

        {/* Dropdown1: choose SDGs vs Targets */}
        <div className="mb-4">
          <label className="block mb-1 font-medium">Type of search:</label>
          <select
            className="border rounded px-3 py-2 w-full max-w-xs"
            value={mode}
            onChange={e => { setMode(e.target.value); setSel([]) }}
          >
            <option value="sdgs">SDGs</option>
            <option value="targets">Targets</option>
          </select>
        </div>

        {/* Selection1/2: multi-select list of SDGs or Targets */}
        <div className="mb-4">
          <label className="block mb-1 font-medium">
            Select one or multiple {mode === 'sdgs' ? 'SDGs' : 'Targets'}:
          </label>
          <select
            multiple
            size={6}
            className="border rounded w-full p-2"
            value={sel}
            onChange={e => {
              const selected = Array.from(e.target.selectedOptions).map(o => o.value)
              setSel(selected)
            }}
          >
            {options.map(opt => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
        </div>

        {/* Keywords */}
        <div className="mb-6">
          <label className="block mb-1 font-medium">Keywords query:</label>
          <textarea
            rows={5}
            className="border rounded w-full p-2"
            value={keywords}
            onChange={e => setKeywords(e.target.value)}
            placeholder="Enter one keyword per line"
          />
        </div>

        {/* Search button */}
        <button
          className="px-6 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition"
          onClick={onSearch}
        >
          Search
        </button>
      </div>
    </div>
  )
}
