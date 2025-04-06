import React, { useState, useEffect } from 'react';
import { Layout } from '../components/layout/layout';
import { Button } from '../components/ui/button';
import { Search, RefreshCw, AlertTriangle, Check, Loader2 } from 'lucide-react';
import { truncate } from '../lib/utils';

// Mock data for crawl jobs
const mockCrawlJobs = [
  {
    id: 1,
    url: 'https://darkforum.example.com/threats',
    status: 'completed',
    createdAt: '2023-11-05T10:23:15Z',
    completedAt: '2023-11-05T10:25:30Z',
    resultCount: 4,
  },
  {
    id: 2,
    url: 'https://t.me/s/cyberthreats',
    status: 'in_progress',
    createdAt: '2023-11-05T11:15:22Z',
    completedAt: null,
    resultCount: 0,
  },
  {
    id: 3,
    url: 'https://leaksite.example.net/dumps',
    status: 'completed',
    createdAt: '2023-11-04T14:45:22Z',
    completedAt: '2023-11-04T14:48:12Z',
    resultCount: 7,
  },
  {
    id: 4,
    url: 'https://hackermarket.onion.example/listings',
    status: 'completed',
    createdAt: '2023-11-03T08:12:44Z',
    completedAt: '2023-11-03T08:19:28Z',
    resultCount: 5,
  },
  {
    id: 5,
    url: 'https://pasteboard.example.io/paste123',
    status: 'failed',
    createdAt: '2023-11-02T19:34:55Z',
    completedAt: '2023-11-02T19:35:10Z',
    resultCount: 0,
  },
];

// Mock data for crawl results
const mockCrawlResults = {
  1: [
    {
      id: 101,
      url: 'https://darkforum.example.com/threads/new-zero-day',
      title: 'New Zero-Day Exploit Discussion',
      content: 'I\'ve discovered a new zero-day vulnerability in Windows Server 2022 that allows remote code execution. Looking for buyers.',
      contentType: 'text/html',
    },
    {
      id: 102,
      url: 'https://darkforum.example.com/threads/ransomware-attack',
      title: 'Upcoming Ransomware Campaign',
      content: 'Planning a new ransomware campaign targeting healthcare organizations in December. Sophisticated tactics to bypass most EDR solutions.',
      contentType: 'text/html',
    },
  ],
  3: [
    {
      id: 301,
      url: 'https://leaksite.example.net/dumps/tech-company-breach',
      title: 'Corporate Database Dump - Fortune 500 Company',
      content: 'Complete dump of employee records and customer data from a major Fortune 500 tech company. Includes emails, hashed passwords, and personal information.',
      contentType: 'text/plain',
    },
    {
      id: 302,
      url: 'https://leaksite.example.net/dumps/healthcare-data',
      title: 'Healthcare Provider Data Breach',
      content: 'Patient records and medical histories from a major healthcare provider. Over 500,000 records including SSNs and insurance details.',
      contentType: 'text/plain',
    },
  ],
};

export default function CrawlPage() {
  const [crawlJobs, setCrawlJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [crawlResults, setCrawlResults] = useState([]);
  const [newUrl, setNewUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // In a real implementation, you would fetch data from the API here
  useEffect(() => {
    setIsLoading(true);
    
    // Simulate API delay
    const timer = setTimeout(() => {
      setCrawlJobs(mockCrawlJobs);
      setIsLoading(false);
    }, 500);
    
    return () => clearTimeout(timer);
  }, []);

  // Load crawl results when a job is selected
  useEffect(() => {
    if (selectedJob) {
      // In a real implementation, you would fetch this from the API
      setCrawlResults(mockCrawlResults[selectedJob.id] || []);
    } else {
      setCrawlResults([]);
    }
  }, [selectedJob]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!newUrl) return;
    
    setIsSubmitting(true);
    
    // Simulate API call to start a new crawl
    setTimeout(() => {
      const newJob = {
        id: Math.max(...crawlJobs.map(job => job.id)) + 1,
        url: newUrl,
        status: 'pending',
        createdAt: new Date().toISOString(),
        completedAt: null,
        resultCount: 0,
      };
      
      setCrawlJobs([newJob, ...crawlJobs]);
      setNewUrl('');
      setIsSubmitting(false);
      
      // Simulate the job starting after a delay
      setTimeout(() => {
        setCrawlJobs(prevJobs => 
          prevJobs.map(job => 
            job.id === newJob.id ? { ...job, status: 'in_progress' } : job
          )
        );
        
        // Simulate job completion after another delay
        setTimeout(() => {
          setCrawlJobs(prevJobs => 
            prevJobs.map(job => 
              job.id === newJob.id ? 
              { 
                ...job, 
                status: 'completed', 
                completedAt: new Date().toISOString(),
                resultCount: Math.floor(Math.random() * 5) + 1
              } : job
            )
          );
        }, 7000);
      }, 2000);
    }, 1000);
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'completed':
        return (
          <div className="flex items-center bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
            <Check className="h-3 w-3 mr-1" /> Completed
          </div>
        );
      case 'in_progress':
        return (
          <div className="flex items-center bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
            <Loader2 className="h-3 w-3 mr-1 animate-spin" /> In Progress
          </div>
        );
      case 'pending':
        return (
          <div className="flex items-center bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded">
            <RefreshCw className="h-3 w-3 mr-1" /> Pending
          </div>
        );
      case 'failed':
        return (
          <div className="flex items-center bg-red-100 text-red-800 text-xs px-2 py-1 rounded">
            <AlertTriangle className="h-3 w-3 mr-1" /> Failed
          </div>
        );
      default:
        return (
          <div className="flex items-center bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded">
            {status}
          </div>
        );
    }
  };

  return (
    <Layout title="Web Crawler | SEER">
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h1 className="text-3xl font-bold tracking-tight">Web Crawler</h1>
          <form onSubmit={handleSubmit} className="flex gap-2 w-full sm:w-auto">
            <div className="relative rounded-md shadow-sm flex-1">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-4 w-4 text-muted-foreground" />
              </div>
              <input
                type="text"
                value={newUrl}
                onChange={(e) => setNewUrl(e.target.value)}
                className="block w-full rounded-md border-0 py-1.5 pl-10 ring-1 ring-inset ring-input bg-background text-foreground sm:text-sm sm:leading-6"
                placeholder="Enter URL to crawl..."
                disabled={isSubmitting}
              />
            </div>
            <Button type="submit" disabled={isSubmitting || !newUrl}>
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Crawling...
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  Crawl
                </>
              )}
            </Button>
          </form>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          <div className="md:col-span-1 space-y-4">
            <div className="rounded-lg border bg-card text-card-foreground shadow-sm">
              <div className="p-4 border-b">
                <h3 className="text-lg font-medium">Crawl Jobs</h3>
              </div>
              <div className="divide-y max-h-[500px] overflow-y-auto">
                {isLoading ? (
                  <div className="p-8 flex justify-center">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                  </div>
                ) : crawlJobs.length === 0 ? (
                  <div className="p-6 text-center text-muted-foreground">
                    No crawl jobs found
                  </div>
                ) : (
                  crawlJobs.map((job) => (
                    <div 
                      key={job.id} 
                      className={`p-4 hover:bg-muted/50 cursor-pointer transition-colors ${
                        selectedJob?.id === job.id ? 'bg-muted' : ''
                      }`}
                      onClick={() => setSelectedJob(job)}
                    >
                      <div className="flex justify-between items-start">
                        <div className="max-w-[70%]">
                          <div className="font-medium truncate">{job.url}</div>
                          <div className="text-xs text-muted-foreground mt-1">
                            {new Date(job.createdAt).toLocaleString()}
                          </div>
                        </div>
                        {getStatusBadge(job.status)}
                      </div>
                      {job.resultCount > 0 && (
                        <div className="mt-2 text-xs text-muted-foreground">
                          {job.resultCount} results found
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          <div className="md:col-span-2">
            <div className="rounded-lg border bg-card text-card-foreground shadow-sm h-full">
              <div className="p-4 border-b">
                <h3 className="text-lg font-medium">
                  {selectedJob ? `Results for ${selectedJob.url}` : 'Crawl Results'}
                </h3>
              </div>
              <div className="p-4">
                {!selectedJob ? (
                  <div className="text-center py-12 text-muted-foreground">
                    Select a job to view results
                  </div>
                ) : selectedJob.status === 'in_progress' || selectedJob.status === 'pending' ? (
                  <div className="text-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground">Job is in progress...</p>
                  </div>
                ) : selectedJob.status === 'failed' ? (
                  <div className="text-center py-12">
                    <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-4" />
                    <p className="text-muted-foreground">Job failed to complete</p>
                  </div>
                ) : crawlResults.length === 0 ? (
                  <div className="text-center py-12 text-muted-foreground">
                    No results found
                  </div>
                ) : (
                  <div className="space-y-4">
                    {crawlResults.map((result) => (
                      <div key={result.id} className="rounded-lg border p-4">
                        <h4 className="font-medium mb-2">{result.title}</h4>
                        <div className="text-xs text-muted-foreground mb-2">{result.url}</div>
                        <p className="text-sm text-muted-foreground">{truncate(result.content, 200)}</p>
                        <div className="mt-4 flex justify-between">
                          <div className="text-xs text-muted-foreground">
                            Content Type: <span className="font-mono">{result.contentType}</span>
                          </div>
                          <Button variant="outline" size="sm">
                            Analyze Threat
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
} 