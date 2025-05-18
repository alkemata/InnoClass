import React from 'react';
import TopBar from './components/TopBar';
import SearchPage from './pages/SearchPage';

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <TopBar />
      <div className="p-4">
        <SearchPage />
      </div>
    </div>
  );
}