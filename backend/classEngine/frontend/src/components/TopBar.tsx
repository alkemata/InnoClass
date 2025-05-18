import React from 'react';

export default function TopBar() {
  return (
    <header className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto flex items-center p-4 space-x-4">
        <img src="/logo.png" alt="Logo" className="h-8 w-auto" />
        <h1 className="text-xl font-semibold">Search Engine</h1>
      </div>
    </header>
  );
}