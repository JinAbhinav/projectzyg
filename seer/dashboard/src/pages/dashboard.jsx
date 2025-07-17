import React, { useState, useEffect } from 'react';
import { Layout } from '../components/layout/layout';
import { Button } from '../components/ui/button';
import { Shield, AlertTriangle, Search, Activity, Zap, Loader2, CheckCircle, XCircle, HelpCircle, Globe, BarChart, Network, Calendar, Target, ChevronRight } from 'lucide-react';
import { truncate, getSeverityColor } from '../lib/utils';
import { useRouter } from 'next/router';
import { getThreats } from '../lib/threat-service';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../components/ui/card';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';
const GRAPH_DATA_URL = '/api/graph/data';

const fetchIpReputation = async (ipAddress) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/v1/enrich/ip/${ipAddress}`);
    return response.data;
  } catch (error) {
    console.error("Error fetching IP reputation:", error);
    throw new Error(error.response?.data?.detail || "Failed to fetch IP reputation");
  }
};

const StatsCard = ({ icon: Icon, title, value, className, isLoading }) => (
  <div className="rounded-lg border bg-card text-card-foreground shadow-sm p-6">
    <div className="flex items-center justify-between space-y-0 pb-2">
      <h3 className="tracking-tight text-sm font-medium">{title}</h3>
      {isLoading ? (
        <Loader2 className={`h-4 w-4 text-muted-foreground animate-spin`} />
      ) : (
        <Icon className={`h-4 w-4 ${className || 'text-muted-foreground'}`} />
      )}
    </div>
    <div className="text-2xl font-bold">
      {isLoading ? '-' : (value ?? 'N/A')}
    </div>
  </div>
);

export default function Dashboard() {
  const [threatStats, setThreatStats] = useState({ totalThreats: 0, criticalThreats: 0, highThreats: 0 });
  const [graphEdgeCount, setGraphEdgeCount] = useState(0);
  const [allThreats, setAllThreats] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const router = useRouter();
  const [isMounted, setIsMounted] = useState(false);

  const [ipToTest, setIpToTest] = useState("");
  const [ipTestResult, setIpTestResult] = useState(null);
  const [isIpTestLoading, setIsIpTestLoading] = useState(false);
  const [ipTestError, setIpTestError] = useState(null);

  useEffect(() => {
    setIsMounted(true);

    const loadDashboardData = async () => {
      setIsLoading(true);
      setError(null);
      setGraphEdgeCount(0);
      try {
        const [threatsResult, graphResult] = await Promise.allSettled([
          getThreats(100),
          fetch(GRAPH_DATA_URL)
        ]);

        let fetchedThreats = [];
        let edgeCount = 0;

        if (threatsResult.status === 'fulfilled') {
          fetchedThreats = threatsResult.value;
          const stats = {
            totalThreats: fetchedThreats.length,
            criticalThreats: fetchedThreats.filter(t => t.severity === 'CRITICAL').length,
            highThreats: fetchedThreats.filter(t => t.severity === 'HIGH').length,
          };
          setThreatStats(stats);
          setAllThreats(fetchedThreats);
        } else {
          console.error("Failed to load threats:", threatsResult.reason);
          setError(prev => prev ? `${prev}; Failed to load threats.` : 'Failed to load threats.');
          setThreatStats({ totalThreats: 0, criticalThreats: 0, highThreats: 0 });
          setAllThreats([]);
        }

        if (graphResult.status === 'fulfilled') {
          const response = graphResult.value;
          if (response.ok) {
            const data = await response.json();
            edgeCount = data.links?.length ?? 0;
          } else {
             console.error(`Failed to load graph data: HTTP ${response.status}`);
             setError(prev => prev ? `${prev}; Failed to load graph stats.` : 'Failed to load graph stats.');
          }
        } else {
           console.error("Failed to load graph data:", graphResult.reason);
           setError(prev => prev ? `${prev}; Failed to load graph stats.` : 'Failed to load graph stats.');
        }
        
        setGraphEdgeCount(edgeCount);

      } catch (err) {
        console.error("Failed to load dashboard data:", err);
        setError(err.message || 'Failed to load data.');
        setThreatStats({ totalThreats: 0, criticalThreats: 0, highThreats: 0 });
        setAllThreats([]);
        setGraphEdgeCount(0);
      } finally {
        setIsLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  const handleGoToScanPage = () => {
    router.push('/scan');
  };

  const handleGoToHostExplorer = () => {
    router.push('/host-explorer');
  };

  const handleIpTest = async (e) => {
    e.preventDefault();
    if (!ipToTest) {
      toast.error("Please enter an IP address to test.");
      return;
    }
    setIsIpTestLoading(true);
    setIpTestResult(null);
    setIpTestError(null);
    try {
      const result = await fetchIpReputation(ipToTest);
      if (result.error) {
        setIpTestError(result.error);
        toast.error(`IP Test Error: ${result.error}`);
      } else {
        setIpTestResult(result);
        toast.success(`IP reputation fetched for ${ipToTest}`);
      }
    } catch (err) {
      setIpTestError(err.message);
      toast.error(`IP Test Failed: ${err.message}`);
    } finally {
      setIsIpTestLoading(false);
    }
  };

  return (
    <Layout title="Dashboard | SEER">
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <div className="flex space-x-2">
            <Button onClick={handleGoToScanPage}>
              <Zap className="mr-2 h-4 w-4" />
              Web Check Tool
            </Button>
            <Button onClick={handleGoToHostExplorer} variant="outline">
              <Globe className="mr-2 h-4 w-4" />
              Host Explorer
            </Button>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StatsCard 
            icon={AlertTriangle} 
            title="Total Threats" 
            value={threatStats.totalThreats} 
            className="text-muted-foreground"
            isLoading={isLoading}
          />
          <StatsCard 
            icon={AlertTriangle} 
            title="Critical Threats" 
            value={threatStats.criticalThreats} 
            className="text-red-500"
            isLoading={isLoading}
          />
          <StatsCard 
            icon={AlertTriangle} 
            title="High Severity Threats" 
            value={threatStats.highThreats} 
            className="text-yellow-500"
            isLoading={isLoading}
          />
          <StatsCard 
            icon={Network} 
            title="Correlations Made" 
            value={graphEdgeCount} 
            className="text-indigo-500"
            isLoading={isLoading}
          />
        </div>

        <div className="rounded-lg border bg-card text-card-foreground shadow-sm">
          <div className="p-6 flex flex-col space-y-4">
            <h3 className="text-lg font-medium">Recent Threats</h3>
            {isLoading && (
              <div className="py-8 flex justify-center"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>
            )}
            {error && (
              <div className="py-4 text-center text-red-600">Error: {error}</div>
            )}
            {!isLoading && !error && allThreats.length === 0 && (
              <div className="py-4 text-center text-muted-foreground">No threats found.</div>
            )}
            {!isLoading && !error && allThreats.length > 0 && (
              <div className="divide-y">
                {allThreats.slice(0, 3).map((threat) => (
                  <div key={threat.id} className="py-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="flex items-center space-x-2">
                          <div className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(threat.severity)}`}>
                            {threat.severity}
                          </div>
                          <h4 className="font-medium">{threat.title || 'Untitled Threat'}</h4>
                        </div>
                        <p className="mt-1 text-sm text-muted-foreground">
                          {truncate(threat.description || 'No description', 100)}
                        </p>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {isMounted ? new Date(threat.created_at).toLocaleDateString() : '...'}
                      </div>
                    </div>
                    <div className="mt-2 flex items-center text-sm">
                      <span className="text-muted-foreground mr-2">Confidence:</span>
                      <div className="w-full max-w-24 bg-secondary rounded-full h-2">
                        <div 
                          className="bg-primary h-2 rounded-full" 
                          style={{ width: `${(threat.confidence || 0) * 100}%` }}
                        ></div>
                      </div>
                      <span className="ml-2 text-xs">{((threat.confidence || 0) * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
            <Button variant="outline" className="mt-2 w-full" onClick={() => router.push('/threats')}>View All Threats</Button>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-lg border bg-card text-card-foreground shadow-sm">
            <div className="p-6">
              <h3 className="text-lg font-medium mb-4">Recent Crawl Jobs</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center p-2 rounded-lg bg-muted">
                  <div className="flex items-center">
                    <Search className="h-4 w-4 mr-2 text-muted-foreground" />
                    <span>darkforum.example.com</span>
                  </div>
                  <div className="text-xs bg-green-100 text-green-800 rounded px-2 py-1">
                    Completed
                  </div>
                </div>
                <div className="flex justify-between items-center p-2 rounded-lg bg-muted">
                  <div className="flex items-center">
                    <Search className="h-4 w-4 mr-2 text-muted-foreground" />
                    <span>t.me/s/cyberthreats</span>
                  </div>
                  <div className="text-xs bg-yellow-100 text-yellow-800 rounded px-2 py-1">
                    In Progress
                  </div>
                </div>
                <div className="flex justify-between items-center p-2 rounded-lg bg-muted">
                  <div className="flex items-center">
                    <Search className="h-4 w-4 mr-2 text-muted-foreground" />
                    <span>leaksite.example.net</span>
                  </div>
                  <div className="text-xs bg-green-100 text-green-800 rounded px-2 py-1">
                    Completed
                  </div>
                </div>
              </div>
              <Button variant="outline" className="mt-4 w-full">View All Crawl Jobs</Button>
            </div>
          </div>
          
          <div className="rounded-lg border bg-card text-card-foreground shadow-sm">
            <div className="p-6">
              <h3 className="text-lg font-medium mb-4">System Status</h3>
              <div className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-sm">API Server</span>
                  <div className="flex items-center">
                    <div className="h-2 w-2 rounded-full bg-green-500 mr-2"></div>
                    <span className="text-sm">Operational</span>
                  </div>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Crawler</span>
                  <div className="flex items-center">
                    <div className="h-2 w-2 rounded-full bg-green-500 mr-2"></div>
                    <span className="text-sm">Operational</span>
                  </div>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">NLP Engine</span>
                  <div className="flex items-center">
                    <div className="h-2 w-2 rounded-full bg-green-500 mr-2"></div>
                    <span className="text-sm">Operational</span>
                  </div>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Database</span>
                  <div className="flex items-center">
                    <div className="h-2 w-2 rounded-full bg-green-500 mr-2"></div>
                    <span className="text-sm">Operational</span>
                  </div>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Alert System</span>
                  <div className="flex items-center">
                    <div className="h-2 w-2 rounded-full bg-green-500 mr-2"></div>
                    <span className="text-sm">Operational</span>
                  </div>
                </div>
              </div>
              <div className="mt-4 p-3 bg-muted rounded-lg text-xs text-center">
                {isMounted ? new Date().toLocaleString() : '...'}
              </div>
            </div>
          </div>

          <div className="rounded-lg border bg-card text-card-foreground shadow-sm">
            <form onSubmit={handleIpTest}>
              <CardHeader>
                <CardTitle>IP Reputation Checker</CardTitle>
                <CardDescription>Check IP reputation using AbuseIPDB.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="ipToTest">IP Address</Label>
                  <Input 
                    id="ipToTest"
                    placeholder="Enter IP address (e.g., 1.1.1.1)"
                    value={ipToTest}
                    onChange={(e) => setIpToTest(e.target.value)}
                  />
                </div>
                {ipTestResult && !ipTestError && (
                  <div className="space-y-2 p-3 bg-muted rounded-md text-sm">
                    <h4 className="font-medium mb-1">Result for: {ipTestResult.ip_address}</h4>
                    <p><strong>Confidence Score:</strong> <span className={`${ipTestResult.abuse_confidence_score > 50 ? 'text-red-500' : 'text-green-500'} font-bold`}>{ipTestResult.abuse_confidence_score}%</span></p>
                    <p><strong>Total Reports:</strong> {ipTestResult.total_reports}</p>
                    <p><strong>Country:</strong> {ipTestResult.country_code || 'N/A'} <img src={`https://flagsapi.com/${ipTestResult.country_code}/flat/24.png`} alt={ipTestResult.country_code} className="inline h-4 ml-1" onError={(e) => e.target.style.display='none'} /></p>
                    <p><strong>ISP:</strong> {ipTestResult.isp || 'N/A'}</p>
                    <p><strong>Domain:</strong> {ipTestResult.domain || 'N/A'}</p>
                    <p><strong>Last Reported:</strong> {ipTestResult.last_reported_at ? new Date(ipTestResult.last_reported_at).toLocaleString() : 'N/A'}</p>
                    <p><strong>Public IP:</strong> {ipTestResult.is_public ? <CheckCircle className="inline h-4 w-4 text-green-500" /> : <XCircle className="inline h-4 w-4 text-red-500" />}</p>
                  </div>
                )}
                {ipTestError && (
                  <div className="p-3 bg-destructive/20 text-destructive-foreground rounded-md text-sm">
                    <p><strong>Error:</strong> {ipTestError}</p>
                  </div>
                )}
              </CardContent>
              <CardFooter>
                <Button type="submit" className="w-full" disabled={isIpTestLoading || !ipToTest}>
                  {isIpTestLoading ? (
                    <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Checking...</>
                  ) : (
                    <><Search className="mr-2 h-4 w-4" /> Check IP</>
                  )}
                </Button>
              </CardFooter>
            </form>
          </div>
        </div>
      </div>
    </Layout>
  );
} 