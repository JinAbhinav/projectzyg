import React, { useState, useEffect } from 'react';
import { Layout } from '../components/layout/layout';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { ThreatResult } from '../components/results/threat-result';
import { JsonViewer } from '../components/ui/json-viewer';
import { Bot, Brain, FileText, Upload, AlertTriangle, Check, X } from 'lucide-react';

// Import parser and local storage utilities
import { parseContent } from '../lib/parser-service';
import { getThreats, saveThreat } from '../lib/local-storage';

// Mock crawl data
const mockCrawl1 = {
  job_id: 1001,
  url: "http://darkforum.local/thread=123",
  status: "completed",
  results: [
    {
      id: 1,
      url: "http://darkforum.local/thread=123",
      title: "New Exploit Discussion - CVE-2024-XXXX",
      content: "Discussion about exploiting CVE-2024-XXXX targeting financial institutions. PoC might be available soon. Watch out for connections to 192.168.1.100.",
      content_type: "text/plain",
      metadata: {
        timestamp: "2024-08-15T10:30:00Z",
        source_type: "forum",
        extracted_iocs: {
          cves: ["CVE-2024-XXXX"],
          ips: ["192.168.1.100"],
          sectors: ["financial"]
        }
      }
    }
  ]
};

const mockCrawl2 = {
  job_id: 1002,
  url: "http://pastesite.local/paste=abc",
  status: "completed",
  results: [
    {
      id: 1,
      url: "http://pastesite.local/paste=abc",
      title: "Credentials Dump",
      content: `Leaked credentials dump from internal system:
      user1:password123
      admin@internal.corp:!P@ssw0rd!
      support@sample.org:pass
      j.doe@internal.corp:Summer2024$
      finance_user:Acc0unt!ngRul3z
      
      This data appears to have been exfiltrated during a recent security incident.
      Affected systems might include the primary authentication server and related databases.
      Immediate password rotation and system audit are recommended for all internal.corp and sample.org users.
      Further investigation is ongoing to determine the full scope of the compromise.
      Initial access vector is suspected to be a phishing campaign targeting employees.
      Monitor network traffic for unusual activity originating from compromised accounts.
      Ensure multi-factor authentication is enabled wherever possible.
      Check logs for access patterns related to these credentials. The leak occurred approximately 48 hours ago.`,
      content_type: "text/plain",
      metadata: {
        timestamp: "2024-08-15T11:00:00Z",
        source_type: "pastebin",
        extracted_iocs: {
          emails: ["admin@internal.corp", "support@sample.org"],
          credentials: ["user1:password123", "admin@internal.corp:!P@ssw0rd!", "support@sample.org:pass"]
        }
      }
    }
  ]
};

export default function ParserPage() {
  const [customContent, setCustomContent] = useState('');
  const [parsedResult, setParsedResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [savedThreats, setSavedThreats] = useState([]);
  const [processingStatus, setProcessingStatus] = useState({ show: false, success: false, message: '' });

  // Fetch saved threats on load
  useEffect(() => {
    fetchSavedThreats();
  }, []);

  const fetchSavedThreats = async () => {
    const { data, error } = await getThreats();
    if (data) {
      setSavedThreats(data);
    }
    if (error) {
      console.error('Error fetching saved threats:', error);
    }
  };

  // Handle custom content parsing
  const handleCustomParse = async () => {
    if (!customContent.trim()) return;
    
    setIsLoading(true);
    setParsedResult(null);
    setProcessingStatus({ show: false, success: false, message: '' });
    
    try {
      // Use the real backend parser service
      const result = await parseContent(customContent, 'Custom input');
      
      if (!result) {
        throw new Error('Parser returned no result.');
      }
      
      setParsedResult(result);
      
      // Save to localStorage
      const threatToSave = {
        ...result,
        source_url: 'Custom input',
        raw_content: customContent,
      };
      const saveResult = await saveThreat(threatToSave);
      
      if (saveResult.error) {
        throw new Error(saveResult.error);
      }
      
      await fetchSavedThreats();
      
      setProcessingStatus({
        show: true,
        success: true,
        message: 'Content analyzed and saved successfully!'
      });
    } catch (error) {
      console.error('Error processing content:', error);
      setProcessingStatus({
        show: true,
        success: false,
        message: `Error: ${error.message || 'Failed to process content'}`
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Handle mock data processing
  const handleProcessMockData = async (mockData) => {
    setIsLoading(true);
    setParsedResult(null);
    setProcessingStatus({ show: false, success: false, message: '' });
    
    // Extract content and source URL from the mock data object
    const contentToParse = mockData.results?.[0]?.content;
    const sourceUrl = mockData.results?.[0]?.url || mockData.url;

    if (!contentToParse || !sourceUrl) {
      setProcessingStatus({ show: true, success: false, message: 'Error: Invalid mock data structure.' });
      setIsLoading(false);
      return;
    }

    try {
      // Use the real backend parser service
      const result = await parseContent(contentToParse, sourceUrl);
      
      if (!result) {
        throw new Error('Parser returned no result.');
      }
      
      setParsedResult(result);
      
      // Save result to localStorage
      const threatToSave = {
        ...result,
        source_url: sourceUrl,
        raw_content: contentToParse,
      };
      const saveResult = await saveThreat(threatToSave);
      
      if (saveResult.error) {
        throw new Error(saveResult.error);
      }
      
      await fetchSavedThreats();
      
      setProcessingStatus({
        show: true,
        success: true,
        message: `Processed 1 result successfully!`
      });
    } catch (error) {
      console.error('Error processing mock data:', error);
      setProcessingStatus({
        show: true,
        success: false,
        message: `Error: ${error.message || 'Failed to process mock data'}`
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Layout title="NLP/LLM Parser Demo | SEER">
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">NLP/LLM Parser Demo</h1>
            <p className="text-muted-foreground mt-1">
              Analyze content with NLP/LLM to detect and extract threat information
            </p>
          </div>
        </div>

        {processingStatus.show && (
          <div className={`p-3 rounded-md ${processingStatus.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
            <div className="flex items-center">
              {processingStatus.success ? (
                <Check className="h-5 w-5 text-green-500 mr-2" />
              ) : (
                <X className="h-5 w-5 text-red-500 mr-2" />
              )}
              <p className={processingStatus.success ? 'text-green-800' : 'text-red-800'}>
                {processingStatus.message}
              </p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="lg:col-span-1">
            <Tabs defaultValue="custom">
              <TabsList className="mb-4">
                <TabsTrigger value="custom">
                  <FileText className="h-4 w-4 mr-2" />
                  Custom Input
                </TabsTrigger>
                <TabsTrigger value="mock1">
                  <Upload className="h-4 w-4 mr-2" />
                  Mock Data 1
                </TabsTrigger>
                <TabsTrigger value="mock2">
                  <Upload className="h-4 w-4 mr-2" />
                  Mock Data 2
                </TabsTrigger>
              </TabsList>
              
              <TabsContent value="custom">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-xl">Custom Content Analysis</CardTitle>
                    <CardDescription>
                      Enter content to analyze with the NLP/LLM parser
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="space-y-2">
                        <Label htmlFor="content">Content</Label>
                        <Textarea
                          id="content"
                          placeholder="Enter content to analyze for threats..."
                          className="min-h-[200px]"
                          value={customContent}
                          onChange={(e) => setCustomContent(e.target.value)}
                        />
                      </div>
                      <Button 
                        onClick={handleCustomParse}
                        disabled={isLoading || !customContent.trim()}
                      >
                        <Brain className="h-4 w-4 mr-2" />
                        {isLoading ? 'Processing...' : 'Analyze Content'}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
              
              <TabsContent value="mock1">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-xl">CVE Discussion</CardTitle>
                    <CardDescription>
                      Process and analyze forum data discussing CVE
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="space-y-2">
                        <div className="border rounded-md p-4 bg-gray-50">
                          <p className="font-medium mb-2">{mockCrawl1.results[0].title}</p>
                          <p className="text-sm text-gray-700">{mockCrawl1.results[0].content}</p>
                          <div className="mt-2 text-xs text-gray-500">Source: {mockCrawl1.url}</div>
                        </div>
                      </div>
                      <Button 
                        onClick={() => handleProcessMockData(mockCrawl1)}
                        disabled={isLoading}
                      >
                        <Bot className="h-4 w-4 mr-2" />
                        {isLoading ? 'Processing...' : 'Process with NLP/LLM'}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
              
              <TabsContent value="mock2">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-xl">Credentials Leak</CardTitle>
                    <CardDescription>
                      Process and analyze leaked credentials data
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="space-y-2">
                        <div className="border rounded-md p-4 bg-gray-50">
                          <p className="font-medium mb-2">{mockCrawl2.results[0].title}</p>
                          <pre className="text-sm text-gray-700 font-mono">{mockCrawl2.results[0].content}</pre>
                          <div className="mt-2 text-xs text-gray-500">Source: {mockCrawl2.url}</div>
                        </div>
                      </div>
                      <Button 
                        onClick={() => handleProcessMockData(mockCrawl2)}
                        disabled={isLoading}
                      >
                        <Bot className="h-4 w-4 mr-2" />
                        {isLoading ? 'Processing...' : 'Process with NLP/LLM'}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
          
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="text-xl">Parsed Results</CardTitle>
                <CardDescription>
                  NLP/LLM parsed threat information
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ThreatResult threatData={parsedResult} isLoading={isLoading} />
              </CardContent>
            </Card>
          </div>
        </div>
        
        <div className="mt-8">
          <Card>
            <CardHeader>
              <CardTitle className="text-xl">Saved Threats</CardTitle>
              <CardDescription>
                Threats processed and saved locally
              </CardDescription>
            </CardHeader>
            <CardContent>
              {savedThreats.length > 0 ? (
                <div className="space-y-4">
                  {savedThreats.slice(0, 3).map((threat, index) => (
                    <div key={index} className="p-4 border rounded-md">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h3 className="font-medium">{threat.title || 'Untitled Threat'}</h3>
                          <p className="text-sm text-gray-500">{threat.source_url}</p>
                        </div>
                        {threat.severity && (
                          <div>
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              threat.severity === 'CRITICAL' ? 'bg-red-100 text-red-800' :
                              threat.severity === 'HIGH' ? 'bg-orange-100 text-orange-800' :
                              threat.severity === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-green-100 text-green-800'
                            }`}>
                              <AlertTriangle className="mr-1 h-3 w-3" />
                              {threat.severity}
                            </span>
                          </div>
                        )}
                      </div>
                      <p className="text-sm">{
                        threat.description ? 
                          (threat.description.length > 120 ? threat.description.substring(0, 120) + '...' : threat.description) :
                          'No description available'
                      }</p>
                    </div>
                  ))}
                  
                  {savedThreats.length > 3 && (
                    <p className="text-center text-sm text-gray-500">
                      Showing 3 of {savedThreats.length} saved threats
                    </p>
                  )}
                </div>
              ) : (
                <div className="text-center p-8 text-gray-500">
                  No saved threats found. Process data to save threats locally.
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </Layout>
  );
} 