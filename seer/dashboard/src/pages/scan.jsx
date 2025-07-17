import React, { useState, useEffect, useRef } from 'react';
import { Layout } from '../components/layout/layout';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../components/ui/card';
import { AlertTriangle, Check, List, Code, RefreshCw, Loader2, Zap, Search, Brain } from 'lucide-react';
import { Separator } from '../components/ui/separator';
import { startScan, getScanStatus, interpretScanResults } from '../lib/scan-service'; // Added interpretScanResults
// We will add the interpret service later

export default function ScanPage() {
  const [targetUrl, setTargetUrl] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [scanTaskId, setScanTaskId] = useState(null);
  const [scanStatus, setScanStatus] = useState(null); // Stores the full status object { status, message, results, ... }
  // Add state for interpretation
  const [isInterpreting, setIsInterpreting] = useState(false);
  const [interpretation, setInterpretation] = useState(null);
  const [interpretError, setInterpretError] = useState(null);
  
  const pollingIntervalRef = useRef(null);

  // Cleanup polling interval on component unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  // Function to poll scan status
  const pollScanStatus = (taskId) => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }

    pollingIntervalRef.current = setInterval(async () => {
      try {
        const status = await getScanStatus(taskId);
        setScanStatus(status);

        if (status.status === 'completed' || status.status === 'failed') {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
          setIsScanning(false);
          // Reset interpretation when a new scan completes/fails
          setInterpretation(null); 
          setInterpretError(null);
        }
      } catch (error) {
        console.error("Error polling scan status:", error);
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
        setIsScanning(false);
        setScanStatus(prev => ({ 
          ...(prev || {}),
          task_id: taskId, 
          status: 'failed', 
          message: `Error checking status: ${error.message || 'Polling failed'}` 
        }));
      }
    }, 3000); // Poll every 3 seconds
  };

  // Handle Scan Now button click
  const handleWebCheck = async () => {
    if (!targetUrl) return;

    setIsScanning(true);
    setScanStatus(null); // Clear previous status
    setScanTaskId(null);
    setInterpretation(null); // Clear previous interpretation
    setInterpretError(null); // Clear previous error
    
    // Basic validation/cleanup
    let urlToScan = targetUrl.trim();
    if (!urlToScan.startsWith('http://') && !urlToScan.startsWith('https://')) {
      urlToScan = 'http://' + urlToScan;
    }

    setScanStatus({ // Initial status 
      task_id: null,
      status: 'starting',
      message: `Initiating web check for ${urlToScan}...`,
      target_url: urlToScan,
      results: null
    });

    try {
      const response = await startScan(urlToScan);
      setScanTaskId(response.task_id);
      setScanStatus(prev => ({ 
        ...prev, 
        task_id: response.task_id, 
        status: 'pending', 
        message: `Web check task ${response.task_id} scheduled. Checking status...`,
        target_url: response.target_url // Use URL potentially modified by backend
      }));
      pollScanStatus(response.task_id);

    } catch (error) {
      console.error("Error starting web check:", error);
      setScanStatus({
        task_id: null,
        status: 'failed',
        message: `Failed to start web check: ${error.message || 'Unknown error'}`,
        target_url: urlToScan,
        results: null
      }); 
      setIsScanning(false);
    }
  };
  
  // Handle Interpretation Request 
  const handleInterpret = async () => {
    if (!scanTaskId || scanStatus?.status !== 'completed') return;
    
    setIsInterpreting(true);
    setInterpretation(null);
    setInterpretError(null);
    
    try {
      const response = await interpretScanResults(scanTaskId);
      if (response.error) {
        throw new Error(response.error);
      }
      setInterpretation(response.interpretation);
    } catch (error) {
      console.error("Error interpreting results:", error);
      setInterpretError(error.message || "Failed to get interpretation from AI.");
    } finally {
      setIsInterpreting(false);
    }
  };

  // Helper to render results nicely
  const renderScanResults = (results) => {
    if (!results) return null;

    return (
      <div className="mt-4 space-y-3 text-sm">
        {results.error_message && (
            <p className="text-red-600"><strong>Error during check:</strong> {results.error_message}</p>
        )}
         <p><strong>Resolved IP:</strong> {results.resolved_ip || 'N/A'}</p>
         <p><strong>Final URL:</strong> <a href={results.final_url || '#'} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">{results.final_url || 'N/A'}</a></p>
         <p><strong>Status Code:</strong> {results.status_code || 'N/A'}</p>
         
         {results.headers && (
           <div>
             <p className="font-medium mt-2">Response Headers:</p>
             <pre className="mt-1 p-3 text-xs border rounded overflow-x-auto text-gray-700">
               {Object.entries(results.headers)
                 .map(([key, value]) => `${key}: ${value}`)
                 .join('\n')}
             </pre>
           </div>
         )}

         {results.ssl_info && (
            <div>
             <p className="font-medium mt-2">SSL Certificate Info:</p>
             {results.ssl_info.error ? (
               <p className="text-orange-600">SSL Info Error: {results.ssl_info.error}</p>
             ) : (
               <ul className="list-disc pl-5 text-xs">
                 <li><strong>Issuer:</strong> {results.ssl_info.issuer || 'N/A'}</li>
                 <li><strong>Subject:</strong> {results.ssl_info.subject || 'N/A'}</li>
                 <li><strong>Expires:</strong> {results.ssl_info.expires ? new Date(results.ssl_info.expires).toLocaleDateString() : 'N/A'}</li>
               </ul>
             )}
           </div>
         )}
      </div>
    );
  }

  return (
    <Layout title="Web Check | SEER">
      <div className="space-y-6">
        <h1 className="text-3xl font-bold tracking-tight">Web Server Check</h1>
        <p className="text-muted-foreground">
          Enter a URL to perform a basic check on the web server, retrieving headers and SSL information.
        </p>

        <Card>
          <CardHeader>
            <CardTitle>Target URL</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex space-x-2">
              <Input 
                type="text"
                placeholder="e.g., https://example.com or example.com"
                value={targetUrl}
                onChange={(e) => setTargetUrl(e.target.value)}
                disabled={isScanning}
                className="flex-grow"
              />
              <Button onClick={handleWebCheck} disabled={isScanning || !targetUrl}>
                {isScanning ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Search className="mr-2 h-4 w-4" />
                )}
                {isScanning ? 'Checking...' : 'Start Check'}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Status and Results Area */}
        {scanStatus && (
          <Card>
            <CardHeader>
              <CardTitle>Check Status</CardTitle>
              <CardDescription>Task ID: {scanStatus.task_id || 'N/A'} | Target: {scanStatus.target_url}</CardDescription>
            </CardHeader>
            <CardContent>
              <p className={`text-sm font-semibold ${scanStatus.status === 'failed' ? 'text-red-600' : (scanStatus.status === 'completed' ? 'text-green-600' : 'text-blue-600')}`}> 
                Status: {scanStatus.status} 
              </p>
              <p className="text-sm text-muted-foreground mt-1">{scanStatus.message}</p>
              
              {/* Render results when completed */}
              {(scanStatus.status === 'completed' || scanStatus.status === 'failed') && scanStatus.results && renderScanResults(scanStatus.results)}
            </CardContent>
            {/* Add Interpretation section */}
            {scanStatus.status === 'completed' && scanStatus.results && !scanStatus.results.error_message && (
              <CardFooter className="flex-col items-start space-y-2 border-t pt-4">
                <Separator className="mb-2"/>
                <Button variant="outline" size="sm" onClick={handleInterpret} disabled={isInterpreting || !scanTaskId}>
                  {isInterpreting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Brain className="mr-2 h-4 w-4" />}
                  {isInterpreting ? 'Interpreting...' : 'Interpret Results (AI)'}
                </Button>
                {interpretError && (
                  <p className="text-sm text-red-600">Error interpreting: {interpretError}</p>
                )}
                {interpretation && (
                  <div className="mt-2 p-3 border rounded w-full">
                     <h4 className="font-medium mb-2 text-gray-800 text-sm">AI Interpretation:</h4>
                     <p className="text-sm whitespace-pre-wrap text-gray-700">{interpretation}</p>
                   </div>
                )}
              </CardFooter>
            )}
          </Card>
        )}

      </div>
    </Layout>
  );
} 