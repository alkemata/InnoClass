import { forwardRef } from 'react'
import axios from 'axios'
import { ThumbsUp, ThumbsDown } from 'lucide-react'

const ResultCard = forwardRef(({ data }, ref) => {
  const sendFeedback = async (fb) => {
    await axios.post('/api/feedback', {
      doc_id: data.id,
      mode: 'sdgs',      // or pass actual mode via props/context
      feedback: fb
    })
  }

  return (
    <div ref={ref} className="border rounded-lg p-4 bg-white shadow">
      <h3 className="font-bold">{data.title}</h3>
      <p className="my-2 text-gray-700">{data.excerpt}…</p>
      <div className="flex flex-wrap gap-2 text-sm">
        {data.sdgs?.map(s=>
          <span key={s} className="bg-blue-100 px-2 py-1 rounded">{s}</span>
        )}
        {data.targets?.map(t=>
          <span key={t} className="bg-green-100 px-2 py-1 rounded">{t}</span>
        )}
      </div>
      <div className="mt-3 flex gap-4">
        <button onClick={()=>sendFeedback('up')}><ThumbsUp size={20}/></button>
        <button onClick={()=>sendFeedback('down')}><ThumbsDown size={20}/></button>
      </div>
    </div>
  )
})

export default ResultCard
