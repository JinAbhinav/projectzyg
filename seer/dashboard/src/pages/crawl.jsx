import React, { useState, useEffect } from 'react';
import { Layout } from '../components/layout/layout';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../components/ui/card';
import { Label } from '../components/ui/label';
import { Slider } from '../components/ui/slider';
import { Switch } from '../components/ui/switch';
import { Badge } from '../components/ui/badge';
import { Separator } from '../components/ui/separator';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import { Search, AlertTriangle, FileDown, Link2, Globe, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

// Mock API function - in production, this would call the actual API
const startCrawlJob = async (url, keywords, maxDepth, maxPages) => {
  console.log(`Starting crawl job for: ${url}`);
  
  // In a real implementation, this would call the API endpoint
  // For the demo, we'll simulate a successful response
  return {
    job_id: Math.floor(Math.random() * 1000),
    status: "pending",
    url
  };
};

// Mock API function for multiple URLs
const startMultiCrawlJob = async (urls, keywords, maxDepth, maxPagesPerSite) => {
  console.log(`Starting multi-crawl job for ${urls.length} URLs`);
  
  // In a real implementation, this would call the API endpoint
  return {
    job_id: Math.floor(Math.random() * 1000),
    status: "pending",
    url: `${urls[0]} and ${urls.length - 1} other sites`
  };
};

// Mock function to check job status
const getCrawlStatus = async (jobId) => {
  // In a real implementation, this would call the API endpoint
  console.log(`Checking status for job: ${jobId}`);
  
  // Simulate different statuses
  const statuses = ["pending", "in_progress", "in_progress", "completed"];
  const randomIndex = Math.min(3, Math.floor(Math.random() * 4));
  
  return {
    job_id: jobId,
    status: statuses[randomIndex],
    url: "https://example.com"
  };
};

// Mock function to get crawl results
const getCrawlResults = async (jobId) => {
  console.log(`Getting results for job: ${jobId}`);
  
  // In a real implementation, this would call the API endpoint
  // For the demo, we'll return mock data
  return [
    {
      id: 1,
      url: "https://darkforum.example.com/threats",
      title: "New Zero-Day Exploit Discussion",
      content: "# Zero-Day Exploit Discussion\n\nI've discovered a new zero-day vulnerability in Windows Server 2022 that allows remote code execution. The vulnerability affects the HTTP.sys component and can be triggered remotely without authentication.\n\n## Technical Details\n\nThe vulnerability is a memory corruption issue in the HTTP request parsing logic. By sending specially crafted packets to the server, an attacker can execute arbitrary code with SYSTEM privileges.\n\n```\nPOC Code (Do not distribute):\nPOST /vulnerable.aspx HTTP/1.1\nHost: target\nContent-Type: application/x-www-form-urlencoded\nContent-Length: 4096\n\n[PAYLOAD REDACTED]\n```\n\nI'm looking for serious buyers only. Starting price is 120k USD in XMR.",
      content_type: "text/markdown",
      metadata: {
        crawled_at: "2023-04-06T10:15:22.000Z",
        links: ["https://darkforum.example.com/profiles/zeroday", "https://darkforum.example.com/buy"],
        depth: 1,
        results_dir: "/crawled_data/darkforum.example.com_20230406_101522"
      },
      results_dir: "/crawled_data/darkforum.example.com_20230406_101522"
    },
    {
      id: 2, 
      url: "https://hackermarket.onion.example/listings",
      title: "Ransomware as a Service - New Payment Models",
      content: "# Ransomware as a Service - Premium Offering\n\nOur ransomware service now offers a 70/30 split with affiliates. Target finance, healthcare, and education sectors for maximum returns.\n\n## Features\n\n- Fully automated encryption\n- Secure payment portal\n- Customer support for victims\n- Double extortion with data exfiltration\n\n## Terms\n\n- 70% of ransom to affiliates\n- 30% to the platform\n- Minimum ransom amount: 10 BTC\n- No targeting of critical infrastructure in CIS countries\n\nContact admin for access to the affiliate program. Serious inquiries only.",
      content_type: "text/markdown",
      metadata: {
        crawled_at: "2023-04-06T10:16:05.000Z",
        links: ["https://hackermarket.onion.example/contact", "https://hackermarket.onion.example/affiliate"],
        depth: 1,
        results_dir: "/crawled_data/hackermarket.onion.example_20230406_101605"
      },
      results_dir: "/crawled_data/hackermarket.onion.example_20230406_101605"
    }
  ];
};

export default function CrawlPage() {
  // State for single URL crawler
  const [url, setUrl] = useState("");
  const [keywords, setKeywords] = useState("");
  const [maxDepth, setMaxDepth] = useState(2);
  const [maxPages, setMaxPages] = useState(10);
  const [crawlDarkWeb, setCrawlDarkWeb] = useState(false);
  
  // State for multiple URL crawler
  const [multipleUrls, setMultipleUrls] = useState("");
  const [multiKeywords, setMultiKeywords] = useState("");
  const [multiMaxDepth, setMultiMaxDepth] = useState(1);
  const [multiMaxPages, setMultiMaxPages] = useState(5);
  
  // State for current job
  const [isLoading, setIsLoading] = useState(false);
  const [currentJobId, setCurrentJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [results, setResults] = useState([]);
  const [selectedResult, setSelectedResult] = useState(null);
  
  // Check job status periodically when a job is running
  useEffect(() => {
    let intervalId;
    
    if (currentJobId && jobStatus && jobStatus !== "completed" && jobStatus !== "failed") {
      intervalId = setInterval(async () => {
        try {
          const status = await getCrawlStatus(currentJobId);
          setJobStatus(status.status);
          
          if (status.status === "completed") {
            const jobResults = await getCrawlResults(currentJobId);
            setResults(jobResults);
            toast.success("Crawl job completed successfully!");
            setIsLoading(false);
          } else if (status.status === "failed") {
            toast.error("Crawl job failed. Please try again.");
            setIsLoading(false);
          }
        } catch (error) {
          console.error("Error checking job status:", error);
        }
      }, 3000);
    }
    
    return () => clearInterval(intervalId);
  }, [currentJobId, jobStatus]);
  
  // Handle form submission for single URL
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!url) {
      toast.error("Please enter a URL to crawl");
      return;
    }
    
    setIsLoading(true);
    setResults([]);
    setSelectedResult(null);
    
    try {
      // Parse keywords from comma-separated string
      const keywordsList = keywords.split(",")
        .map(k => k.trim())
        .filter(k => k.length > 0);
      
      const response = await startCrawlJob(
        url,
        keywordsList.length > 0 ? keywordsList : null,
        maxDepth,
        maxPages
      );
      
      setCurrentJobId(response.job_id);
      setJobStatus(response.status);
      toast.info(`Started crawl job #${response.job_id}`);
    } catch (error) {
      console.error("Error starting crawl job:", error);
      toast.error("Failed to start crawl job");
      setIsLoading(false);
    }
  };
  
  // Handle form submission for multiple URLs
  const handleMultiSubmit = async (e) => {
    e.preventDefault();
    
    if (!multipleUrls) {
      toast.error("Please enter URLs to crawl");
      return;
    }
    
    setIsLoading(true);
    setResults([]);
    setSelectedResult(null);
    
    try {
      // Parse URLs from newline-separated string
      const urlList = multipleUrls.split("\n")
        .map(u => u.trim())
        .filter(u => u.length > 0);
      
      if (urlList.length === 0) {
        toast.error("No valid URLs found");
        setIsLoading(false);
        return;
      }
      
      // Parse keywords from comma-separated string
      const keywordsList = multiKeywords.split(",")
        .map(k => k.trim())
        .filter(k => k.length > 0);
      
      const response = await startMultiCrawlJob(
        urlList,
        keywordsList.length > 0 ? keywordsList : null,
        multiMaxDepth,
        multiMaxPages
      );
      
      setCurrentJobId(response.job_id);
      setJobStatus(response.status);
      toast.info(`Started multi-site crawl job #${response.job_id}`);
    } catch (error) {
      console.error("Error starting multi-site crawl job:", error);
      toast.error("Failed to start multi-site crawl job");
      setIsLoading(false);
    }
  };
  
  // Handle viewing a specific result
  const handleViewResult = (result) => {
    setSelectedResult(result);
  };
  
  // Format URLs for display in results list
  const formatUrl = (url, maxLength = 50) => {
    if (url.length <= maxLength) return url;
    const start = url.substring(0, 30);
    const end = url.substring(url.length - 15);
    return `${start}...${end}`;
  };
  
  return (
    <Layout title="Crawler | SEER">
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold tracking-tight">Web Crawler</h1>
        </div>
        
        <div className="grid gap-6 md:grid-cols-5">
          <div className="space-y-6 md:col-span-2">
            <Tabs defaultValue="single" className="w-full">
              <TabsList className="grid grid-cols-2">
                <TabsTrigger value="single">Single URL</TabsTrigger>
                <TabsTrigger value="multiple">Multiple URLs</TabsTrigger>
              </TabsList>
              
              <TabsContent value="single">
                <Card>
                  <form onSubmit={handleSubmit}>
                    <CardHeader>
                      <CardTitle>Crawl Single URL</CardTitle>
                      <CardDescription>
                        Configure a crawl job for a single website
                      </CardDescription>
                    </CardHeader>
                    
                    <CardContent className="space-y-4">
                      <div className="space-y-2">
                        <Label htmlFor="url">URL to Crawl</Label>
                        <Input
                          id="url"
                          type="url"
                          placeholder="https://example.com"
                          value={url}
                          onChange={(e) => setUrl(e.target.value)}
                          required
                        />
                      </div>
                      
                      <div className="space-y-2">
                        <Label htmlFor="keywords">Keywords (optional, comma-separated)</Label>
                        <Input
                          id="keywords"
                          placeholder="exploit, vulnerability, hack"
                          value={keywords}
                          onChange={(e) => setKeywords(e.target.value)}
                        />
                        <p className="text-xs text-muted-foreground">
                          Pages containing these keywords will be prioritized
                        </p>
                      </div>
                      
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <Label htmlFor="maxDepth">Max Crawl Depth: {maxDepth}</Label>
                          <span className="text-xs text-muted-foreground">(1-5)</span>
                        </div>
                        <Slider
                          id="maxDepth"
                          min={1}
                          max={5}
                          step={1}
                          value={[maxDepth]}
                          onValueChange={(value) => setMaxDepth(value[0])}
                        />
                        <p className="text-xs text-muted-foreground">
                          Higher values will crawl more deeply into the site
                        </p>
                      </div>
                      
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <Label htmlFor="maxPages">Max Pages: {maxPages}</Label>
                          <span className="text-xs text-muted-foreground">(1-50)</span>
                        </div>
                        <Slider
                          id="maxPages"
                          min={1}
                          max={50}
                          step={1}
                          value={[maxPages]}
                          onValueChange={(value) => setMaxPages(value[0])}
                        />
                        <p className="text-xs text-muted-foreground">
                          Limit the total number of pages crawled
                        </p>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <Switch
                          id="darkWeb"
                          checked={crawlDarkWeb}
                          onCheckedChange={setCrawlDarkWeb}
                        />
                        <Label htmlFor="darkWeb">Enable Dark Web Access</Label>
                      </div>
                      
                      {crawlDarkWeb && (
                        <Alert variant="destructive">
                          <AlertTriangle className="h-4 w-4" />
                          <AlertTitle>Warning</AlertTitle>
                          <AlertDescription>
                            Dark web access requires proper configuration and legal compliance.
                            Make sure you have configured Tor access correctly in settings.
                          </AlertDescription>
                        </Alert>
                      )}
                    </CardContent>
                    
                    <CardFooter>
                      <Button 
                        type="submit" 
                        className="w-full" 
                        disabled={isLoading || !url}
                      >
                        {isLoading ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Crawling...
                          </>
                        ) : (
                          <>
                            <Search className="mr-2 h-4 w-4" />
                            Start Crawling
                          </>
                        )}
                      </Button>
                    </CardFooter>
                  </form>
                </Card>
              </TabsContent>
              
              <TabsContent value="multiple">
                <Card>
                  <form onSubmit={handleMultiSubmit}>
                    <CardHeader>
                      <CardTitle>Crawl Multiple URLs</CardTitle>
                      <CardDescription>
                        Configure a multi-site crawl job
                      </CardDescription>
                    </CardHeader>
                    
                    <CardContent className="space-y-4">
                      <div className="space-y-2">
                        <Label htmlFor="multipleUrls">URLs to Crawl (one per line)</Label>
                        <Textarea
                          id="multipleUrls"
                          placeholder="https://example1.com&#10;https://example2.com&#10;https://darksite.onion"
                          rows={4}
                          value={multipleUrls}
                          onChange={(e) => setMultipleUrls(e.target.value)}
                          required
                        />
                      </div>
                      
                      <div className="space-y-2">
                        <Label htmlFor="multiKeywords">Keywords (optional, comma-separated)</Label>
                        <Input
                          id="multiKeywords"
                          placeholder="exploit, vulnerability, hack"
                          value={multiKeywords}
                          onChange={(e) => setMultiKeywords(e.target.value)}
                        />
                      </div>
                      
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <Label htmlFor="multiMaxDepth">Max Crawl Depth: {multiMaxDepth}</Label>
                          <span className="text-xs text-muted-foreground">(1-3)</span>
                        </div>
                        <Slider
                          id="multiMaxDepth"
                          min={1}
                          max={3}
                          step={1}
                          value={[multiMaxDepth]}
                          onValueChange={(value) => setMultiMaxDepth(value[0])}
                        />
                      </div>
                      
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <Label htmlFor="multiMaxPages">Max Pages Per Site: {multiMaxPages}</Label>
                          <span className="text-xs text-muted-foreground">(1-20)</span>
                        </div>
                        <Slider
                          id="multiMaxPages"
                          min={1}
                          max={20}
                          step={1}
                          value={[multiMaxPages]}
                          onValueChange={(value) => setMultiMaxPages(value[0])}
                        />
                      </div>
                      
                      <Alert>
                        <Globe className="h-4 w-4" />
                        <AlertTitle>Information</AlertTitle>
                        <AlertDescription>
                          Onion URLs will automatically use Tor proxy if available.
                          Separate credentials in URLs like: https://username:password@example.com
                        </AlertDescription>
                      </Alert>
                    </CardContent>
                    
                    <CardFooter>
                      <Button 
                        type="submit" 
                        className="w-full" 
                        disabled={isLoading || !multipleUrls}
                      >
                        {isLoading ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Crawling Multiple Sites...
                          </>
                        ) : (
                          <>
                            <Search className="mr-2 h-4 w-4" />
                            Start Multi-Site Crawl
                          </>
                        )}
                      </Button>
                    </CardFooter>
                  </form>
                </Card>
              </TabsContent>
            </Tabs>
            
            {currentJobId && (
              <Card>
                <CardHeader>
                  <CardTitle>Crawl Job #{currentJobId}</CardTitle>
                  <CardDescription>
                    Current job status and information
                  </CardDescription>
                </CardHeader>
                
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">Status:</span>
                    <Badge variant={
                      jobStatus === "completed" ? "success" :
                      jobStatus === "failed" ? "destructive" :
                      jobStatus === "in_progress" ? "default" : "outline"
                    }>
                      {jobStatus || "Unknown"}
                    </Badge>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="font-medium">Pages Crawled:</span>
                    <span>{results.length}</span>
                  </div>
                  
                  {jobStatus === "in_progress" && (
                    <div className="flex justify-center">
                      <Loader2 className="h-8 w-8 animate-spin text-primary" />
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
          
          <div className="md:col-span-3 space-y-6">
            <Card className="h-full flex flex-col">
              <CardHeader>
                <CardTitle>Crawl Results</CardTitle>
                <CardDescription>
                  {results.length ? `${results.length} pages crawled` : "No results yet"}
                </CardDescription>
              </CardHeader>
              
              <div className="flex-1 flex overflow-hidden">
                {results.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-0 w-full overflow-hidden">
                    <div className="border-r overflow-auto max-h-[700px]">
                      <div className="divide-y">
                        {results.map((result) => (
                          <div 
                            key={result.id}
                            className={`p-4 cursor-pointer hover:bg-accent ${
                              selectedResult?.id === result.id ? "bg-muted" : ""
                            }`}
                            onClick={() => handleViewResult(result)}
                          >
                            <div className="font-medium truncate">
                              {result.title}
                            </div>
                            <div className="text-sm text-muted-foreground flex items-center space-x-1">
                              <Globe className="h-3 w-3" />
                              <span>{formatUrl(result.url)}</span>
                            </div>
                            <div className="text-xs text-muted-foreground mt-1">
                              {new Date(result.metadata.crawled_at).toLocaleString()}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    <div className="overflow-auto max-h-[700px]">
                      {selectedResult ? (
                        <div className="p-4 space-y-4">
                          <div>
                            <h3 className="text-lg font-medium">{selectedResult.title}</h3>
                            <a 
                              href={selectedResult.url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-sm text-primary flex items-center hover:underline"
                            >
                              <Link2 className="h-3 w-3 mr-1" />
                              {selectedResult.url}
                            </a>
                          </div>
                          
                          <Separator />
                          
                          <div className="space-y-2">
                            <div className="flex items-center justify-between">
                              <h4 className="font-medium">Metadata</h4>
                              {selectedResult.results_dir && (
                                <Button variant="outline" size="sm">
                                  <FileDown className="h-4 w-4 mr-1" />
                                  Open Folder
                                </Button>
                              )}
                            </div>
                            
                            <div className="bg-muted p-2 rounded-md text-xs">
                              <div><span className="font-medium">Crawled:</span> {new Date(selectedResult.metadata.crawled_at).toLocaleString()}</div>
                              <div><span className="font-medium">Depth:</span> {selectedResult.metadata.depth}</div>
                              <div><span className="font-medium">Links:</span> {selectedResult.metadata.links.length}</div>
                              {selectedResult.results_dir && (
                                <div><span className="font-medium">Storage:</span> {selectedResult.results_dir}</div>
                              )}
                            </div>
                          </div>
                          
                          <Separator />
                          
                          <div className="space-y-2">
                            <h4 className="font-medium">Content</h4>
                            <div className="bg-muted p-4 rounded-md overflow-auto max-h-[400px] whitespace-pre-wrap">
                              <pre className="text-sm font-mono">{selectedResult.content}</pre>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-center justify-center h-full text-muted-foreground">
                          Select a result to view details
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center w-full p-8 text-center">
                    <Search className="h-16 w-16 text-muted-foreground mb-4 opacity-20" />
                    <h3 className="text-lg font-medium">No Crawl Results Yet</h3>
                    <p className="text-muted-foreground">
                      Start a crawl job to see results here
                    </p>
                  </div>
                )}
              </div>
            </Card>
          </div>
        </div>
      </div>
    </Layout>
  );
} 