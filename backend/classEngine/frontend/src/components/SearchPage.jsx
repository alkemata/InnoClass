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

  const toggleOption = (opt) => {
    setSel(s => s.includes(opt) ? s.filter(x=>x!==opt) : [...s, opt])
  }

  const onSearch = () => {
    // pass state via query params or context
    navigate('/results', { state: { mode, sel, keywords } })
  }

  return (
    <div className="max-w-xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">SDG / Target Search</h1>
      <div className="flex gap-4 mb-4">
        <button
          className={`px-4 py-2 rounded ${mode==='sdgs' ? 'bg-blue-500 text-white':'bg-white'}`}
          onClick={()=>{ setMode('sdgs'); setSel([]) }}
        >SDGs</button>
        <button
          className={`px-4 py-2 rounded ${mode==='targets' ? 'bg-blue-500 text-white':'bg-white'}`}
          onClick={()=>{ setMode('targets'); setSel([]) }}
        >Targets</button>
      </div>

      <div className="mb-4">
        <label className="block mb-1">Select {mode.toUpperCase()}:</label>
        <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto border p-2">
          {options.map(opt => (
            <label key={opt} className="flex items-center">
              <input
                type="checkbox"
                className="mr-2"
                checked={sel.includes(opt)}
                onChange={()=>toggleOption(opt)}
              />
              <span>{opt}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="mb-4">
        <label className="block mb-1">Keywords (one per line):</label>
        <textarea
          rows={4}
          className="w-full border p-2"
          value={keywords}
          onChange={e=>setKeywords(e.target.value)}
        />
      </div>

      <button
        onClick={onSearch}
        className="px-6 py-2 bg-green-600 text-white rounded"
      >
        Search
      </button>
    </div>
  )
}
