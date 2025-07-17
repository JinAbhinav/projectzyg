'use client';

import { useState, ChangeEvent, FormEvent } from 'react';

interface AnalysisResult {
  message: string;
  source_document_id?: string;
  graph_update_summary?: {
    nodes_created_or_found: number;
    edges_attempted: number;
    edges_created: number;
    errors: number;
    message: string;
  };
  llm_output?: any; // If you decide to return full LLM output
  error?: string;
  details?: string;
}

export default function ThreatTextAnalyzerCard() {
  const [textToAnalyze, setTextToAnalyze] = useState<string>('');
  const [sourceDocumentId, setSourceDocumentId] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsLoading(true);
    setError(null);
    setAnalysisResult(null);

    if (!textToAnalyze.trim()) {
      setError('Text to analyze cannot be empty.');
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch('/api/analyze_text_for_relationships', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text_to_analyze: textToAnalyze,
          source_document_id: sourceDocumentId || null, // Send null if empty
        }),
      });

      const resultData: AnalysisResult = await response.json();

      if (!response.ok) {
        const errorMsg = resultData.error || resultData.details || `API Error: ${response.status}`;
        throw new Error(errorMsg);
      }

      setAnalysisResult(resultData);
    } catch (err: any) {
      console.error('Analysis API call failed:', err);
      setError(err.message || 'Failed to analyze text. Check console for details.');
      setAnalysisResult(null); // Clear previous results on new error
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white shadow-lg rounded-lg p-6 my-6">
      <h2 className="text-xl font-semibold text-gray-700 mb-4">AI Threat Text Analyzer</h2>
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label htmlFor="textToAnalyze" className="block text-sm font-medium text-gray-700 mb-1">
            Text to Analyze <span className="text-red-500">*</span>
          </label>
          <textarea
            id="textToAnalyze"
            name="textToAnalyze"
            rows={6}
            className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            value={textToAnalyze}
            onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setTextToAnalyze(e.target.value)}
            placeholder="Paste text containing threat information here..."
            required
          />
        </div>

        <div className="mb-4">
          <label htmlFor="sourceDocumentId" className="block text-sm font-medium text-gray-700 mb-1">
            Source Document ID (Optional)
          </label>
          <input
            type="text"
            id="sourceDocumentId"
            name="sourceDocumentId"
            className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            value={sourceDocumentId}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setSourceDocumentId(e.target.value)}
            placeholder="e.g., report-123, crawl-job-456"
          />
        </div>

        <div className="flex items-center justify-end">
          <button
            type="submit"
            disabled={isLoading}
            className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400"
          >
            {isLoading ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Analyzing...
              </>
            ) : (
              'Analyze Text'
            )}
          </button>
        </div>
      </form>

      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-md">
          <p className="font-semibold">Error:</p>
          <p>{error}</p>
        </div>
      )}

      {analysisResult && !error && (
        <div className="mt-6 p-4 border border-gray-200 rounded-md bg-gray-50">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Analysis Complete</h3>
          <p className="text-sm text-gray-600 mb-1">{analysisResult.message}</p>
          {analysisResult.source_document_id && (
            <p className="text-sm text-gray-600 mb-1">Source ID: <span className="font-medium">{analysisResult.source_document_id}</span></p>
          )}
          {analysisResult.graph_update_summary && (
            <div className="mt-2 pt-2 border-t border-gray-200">
              <p className="text-sm text-gray-700 font-medium">Knowledge Graph Update:</p>
              <ul className="list-disc list-inside text-sm text-gray-600 pl-2">
                <li>Nodes Processed/Found: {analysisResult.graph_update_summary.nodes_created_or_found}</li>
                <li>Relationships Attempted: {analysisResult.graph_update_summary.edges_attempted}</li>
                <li>Relationships Created: {analysisResult.graph_update_summary.edges_created}</li>
                {analysisResult.graph_update_summary.errors > 0 && (
                  <li className="text-red-500">Errors during update: {analysisResult.graph_update_summary.errors}</li>
                )}
              </ul>
              <p className="text-xs text-gray-500 mt-1">{analysisResult.graph_update_summary.message}</p>
            </div>
          )}
           {/* Optionally display more details from llm_output if needed */}
        </div>
      )}
    </div>
  );
} 