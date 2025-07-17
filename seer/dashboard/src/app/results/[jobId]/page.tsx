'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation'; // Hook to get dynamic route parameters
// import CrawlResultDetail from '@/components/results/CrawlResultDetail'; 
import CrawlResultDetail from '../../../components/results/CrawlResultDetail'; // Correct relative path

// Reuse the interface defined in the component (or import if shared)
interface ExtractedIOCs {
    emails?: string[];
    ips?: string[];
    cves?: string[];
    urls?: string[];
    domains?: string[];
    credentials?: string[];
    sectors?: string[];
}
interface ResultMetadata {
    timestamp?: string;
    source_type?: string;
    extracted_iocs?: ExtractedIOCs;
}
interface CrawlResultItem {
    id: number;
    url: string;
    title: string;
    content: string;
    content_type?: string;
    metadata: ResultMetadata;
    results_dir?: string;
    file_path?: string;
}

const ResultPage = () => {
    const params = useParams();
    const jobId = params?.jobId as string; // Get jobId from URL, assert as string

    const [resultData, setResultData] = useState<CrawlResultItem | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!jobId) return; // Don't fetch if jobId is not available yet

        const fetchResults = async () => {
            setLoading(true);
            setError(null);
            try {
                // NOTE: Assumes backend is running on localhost:8000
                // In production, use environment variables for the API base URL
                const apiUrl = `http://localhost:8000/api/crawl/${jobId}/results`; 
                console.log(`Fetching results from: ${apiUrl}`);
                
                const response = await fetch(apiUrl);
                
                console.log(`Response status: ${response.status}`);
                if (!response.ok) {
                    const errorData = await response.json();
                    console.error('API Error Data:', errorData);
                    throw new Error(errorData.detail || `Failed to fetch results: ${response.statusText}`);
                }
                
                const data: CrawlResultItem[] = await response.json();
                console.log('Fetched Data:', data);

                if (data && data.length > 0) {
                    setResultData(data[0]); // Display the first result item
                } else {
                    setError('No results found for this job ID.');
                }
            } catch (err: any) {
                console.error('Fetch Error:', err);
                setError(err.message || 'An unexpected error occurred.');
            } finally {
                setLoading(false);
            }
        };

        fetchResults();
    }, [jobId]); // Re-run effect if jobId changes

    if (loading) {
        return (
            <div className="flex justify-center items-center h-screen">
                <p className="text-gray-500 dark:text-gray-400">Loading results for Job ID: {jobId}...</p>
                 {/* Add a spinner later if desired */}
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex flex-col justify-center items-center h-screen text-center px-4">
                <p className="text-red-600 dark:text-red-400 font-semibold">Error loading results for Job ID: {jobId}</p>
                <p className="text-sm text-gray-600 dark:text-gray-300 mt-2">{error}</p>
                <p className="text-xs text-gray-400 dark:text-gray-500 mt-4">Please ensure the backend server is running and the Job ID is correct. Have you loaded the mock data using the POST /mock/process/ endpoint?</p>
            </div>
        );
    }

    if (!resultData) {
        return (
             <div className="flex justify-center items-center h-screen">
                 <p className="text-gray-500 dark:text-gray-400">No result data available for Job ID: {jobId}.</p>
             </div>
        );
    }

    return (
        <div className="container mx-auto p-4 md:p-8">
            <h1 className="text-3xl font-bold mb-6 border-b pb-2 dark:text-white dark:border-gray-700">Crawl Result Details</h1>
            <CrawlResultDetail resultItem={resultData} />
        </div>
    );
};

export default ResultPage; 