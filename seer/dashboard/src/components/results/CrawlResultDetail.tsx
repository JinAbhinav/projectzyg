import React, { useState, useEffect } from 'react';

// Define the structure for a single IOC based on our mock data
interface ExtractedIOCs {
  emails?: string[];
  ips?: string[];
  cves?: string[];
  urls?: string[];
  domains?: string[];
  credentials?: string[];
  sectors?: string[];
}

// Define the structure for the metadata within a result item
interface ResultMetadata {
  timestamp?: string;
  source_type?: string;
  extracted_iocs?: ExtractedIOCs;
  // Add other potential metadata fields if needed
}

// Define the structure for a single result item (page/document) within a crawl job
interface CrawlResultItem {
  id: number;
  url: string;
  title: string;
  content: string;
  content_type?: string;
  metadata: ResultMetadata;
  results_dir?: string; // Keep optional fields from API response
  file_path?: string;
}

// Define the props for our component
interface CrawlResultDetailProps {
  resultItem: CrawlResultItem; // Accepts a single result item
}

const CrawlResultDetail: React.FC<CrawlResultDetailProps> = ({ resultItem }) => {
  const [groupedIOCs, setGroupedIOCs] = useState<Record<string, string[]>>({});

  useEffect(() => {
    const iocs = resultItem.metadata?.extracted_iocs;
    if (iocs) {
      const grouped: Record<string, string[]> = {};
      for (const [type, values] of Object.entries(iocs)) {
        if (values && values.length > 0) {
          grouped[type] = values;
        }
      }
      setGroupedIOCs(grouped);
    } else {
      setGroupedIOCs({});
    }
  }, [resultItem.metadata?.extracted_iocs]);

  const iocCount = Object.values(groupedIOCs).reduce((sum, arr) => sum + arr.length, 0);

  return (
    <div className="w-full border rounded-lg shadow-md p-6 bg-white dark:bg-gray-800 dark:border-gray-700">
      {/* Header Section */}
      <div className="mb-6 border-b pb-4 dark:border-gray-600">
        <h2 className="text-2xl font-bold mb-1 text-gray-900 dark:text-white">{resultItem.title}</h2>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-gray-500 dark:text-gray-400">
          {resultItem.metadata.timestamp && (
            <span className="flex items-center">
              {/* Basic clock icon placeholder */}
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              {new Date(resultItem.metadata.timestamp).toLocaleString()}
            </span>
          )}
          {resultItem.metadata.source_type && (
            <span className="px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
              {resultItem.metadata.source_type}
            </span>
          )}
          <a href={resultItem.url} className="hover:underline truncate max-w-xs flex items-center" target="_blank" rel="noopener noreferrer">
            {/* Basic link icon placeholder */}
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
            {resultItem.url}
          </a>
        </div>
      </div>

      {/* IOC Summary */}
      <div className="mb-4 text-sm text-gray-600 dark:text-gray-300">
        <span>IOCs Found: {iocCount}</span>
      </div>

      <hr className="mb-4 dark:border-gray-600"/>

      {/* Content Section */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-2 text-gray-800 dark:text-gray-200">Content</h3>
        <div className="h-96 overflow-auto w-full rounded border p-4 bg-gray-50 dark:bg-gray-700 dark:border-gray-600">
          <pre className="whitespace-pre-wrap text-sm font-mono text-gray-700 dark:text-gray-300">{resultItem.content || "No content available."}</pre>
        </div>
      </div>
      
      {/* IOCs Section */}
      <div>
         <h3 className="text-lg font-semibold mb-3 text-gray-800 dark:text-gray-200">Indicators of Compromise ({iocCount})</h3>
         {iocCount > 0 ? (
           <div className="space-y-4">
             {Object.entries(groupedIOCs).map(([type, iocs]) => (
               <div key={type} className="space-y-2">
                 <h4 className="font-medium capitalize text-md border-b pb-1 mb-2 text-gray-700 dark:text-gray-300 dark:border-gray-600">{type} ({iocs.length})</h4>
                 <div className="max-h-48 overflow-auto w-full rounded border p-2 bg-gray-50 dark:bg-gray-700 dark:border-gray-600 space-y-1">
                   {iocs.map((iocValue, index) => (
                     <div key={`${type}-${index}`} className="flex items-center justify-between bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 p-2 rounded text-xs font-mono border dark:border-gray-500">
                       <span>{iocValue}</span>
                       {/* Placeholder for copy button */}
                       <button onClick={() => navigator.clipboard.writeText(iocValue)} title="Copy IOC" className="ml-2 px-1 py-0.5 text-xs bg-gray-200 dark:bg-gray-600 rounded hover:bg-gray-300 dark:hover:bg-gray-500">
                         Copy
                       </button>
                     </div>
                   ))}
                 </div>
               </div>
             ))}
           </div>
         ) : (
           <div className="p-6 text-center border rounded bg-gray-50 dark:bg-gray-700 dark:border-gray-600">
             {/* Basic alert icon placeholder */}
             <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 text-gray-400 dark:text-gray-500 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
             <h3 className="font-medium text-md text-gray-700 dark:text-gray-300">No IOCs Found</h3>
             <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">No indicators were extracted from this result's metadata.</p>
           </div>
         )}
      </div>

    </div>
  );
};

export default CrawlResultDetail; 