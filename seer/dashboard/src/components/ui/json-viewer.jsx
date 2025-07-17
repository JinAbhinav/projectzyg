"use client";

import React, { useEffect, useState } from 'react';

export const JsonViewer = ({ data, name = "JSON", collapsed = false, collapseStringsAfterLength = 40 }) => {
  const [mounted, setMounted] = useState(false);
  
  // Use useEffect to ensure component is only rendered client-side
  useEffect(() => {
    setMounted(true);
  }, []);
  
  if (!mounted) {
    return <div className="p-4 border rounded-md bg-gray-100">Loading JSON viewer...</div>;
  }
  
  return (
    <div className="json-viewer-container overflow-auto">
      <pre 
        className="p-4 bg-gray-900 text-gray-100 rounded-md text-sm overflow-auto"
        style={{
          maxHeight: '400px',
        }}
      >
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  );
}; 