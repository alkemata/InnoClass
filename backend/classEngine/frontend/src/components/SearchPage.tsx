import React, { useState } from 'react';

export default function SearchPage() {
  const [mode, setMode] = useState<'SDG' | 'targets'>('SDG');
  const [keyword, setKeyword] = useState('');

  const handleSearch = async () => {
    try {
      const res = await fetch('https://localhost:8000/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // add auth header or CSRF token if needed
        },
        body: JSON.stringify({ mode, keyword }),
        credentials: 'include',
      });
      if (!res.ok) throw new Error('Network response was not ok');
      const data = await res.json();
      console.log(data);
      // handle response
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block mb-1 font-medium">Choose Mode</label>
        <select
          value={mode}
          onChange={(e) => setMode(e.target.value as any)}
          className="w-full max-w-xs p-2 border rounded"
        >
          <option value="SDG">SDG</option>
          <option value="targets">targets</option>
        </select>
      </div>

      <div>
        <label htmlFor="keyword" className="block mb-1 font-medium">keyword search</label>
        <textarea
          id="keyword"
          rows={3}
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          className="w-full p-2 border rounded resize-none"
        />
      </div>

      <div>
        <button
          onClick={handleSearch}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Search
        </button>
      </div>
    </div>
  );
}