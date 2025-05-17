import { useLocation } from 'react-router-dom'
import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import ResultCard from './ResultCard'

export default function ResultsPage() {
  const { state:{ mode, sel, keywords } } = useLocation()
  const [results, setResults] = useState([])
  const [page, setPage] = useState(0)
  const [hasMore, setHasMore] = useState(true)

  const loadMore = useCallback(async () => {
    const res = await axios.post('/api/search', {
      mode,
      selected: sel,
      keywords,
      page
    })
    if (res.data.length < 20) setHasMore(false)
    setResults(r=>[...r, ...res.data])
    setPage(p=>p+1)
  }, [mode, sel, keywords, page])

  useEffect(() => { loadMore() }, [])

  // infinite scroll using IntersectionObserver
  const observer = useRef()
  const lastRef = useCallback(node => {
    if (observer.current) observer.current.disconnect()
    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && hasMore) loadMore()
    })
    if (node) observer.current.observe(node)
  }, [hasMore, loadMore])

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-4">
      <h2 className="text-xl font-semibold">Results</h2>
      {results.map((hit, idx) => (
        <ResultCard
          key={hit.id}
          data={hit}
          ref={idx===results.length-1 ? lastRef : null}
        />
      ))}
      {!hasMore && <p className="text-center text-gray-500">No more results</p>}
    </div>
  )
}
