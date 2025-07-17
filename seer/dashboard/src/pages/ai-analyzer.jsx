import React, { useState, useEffect } from 'react';
import { Layout } from '../components/layout/layout'; // Adjust path if needed
import ThreatTextAnalyzerCard from '../components/ai/ThreatTextAnalyzerCard';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../components/ui/card';
import { DatabaseZap, Library, Loader2, Network, Send } from 'lucide-react'; // Added icons
import { toast } from 'sonner'; // For feedback
import Link from 'next/link'; // For navigation

// API Endpoints
const POPULATE_GRAPH_URL = '/api/graph/populate';
const GRAPH_DATA_URL = '/api/graph/data'; 

export default function AiAnalyzerPage() {
  const [isPopulating, setIsPopulating] = useState(false);
  const [populateStatus, setPopulateStatus] = useState('');
  const [graphStats, setGraphStats] = useState({ nodeCount: '-', edgeCount: '-'});
  const [statsLoading, setStatsLoading] = useState(true);

  // Fetch graph stats on load
  useEffect(() => {
    const fetchStats = async () => {
      setStatsLoading(true);
      try {
        const response = await fetch(GRAPH_DATA_URL);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setGraphStats({ 
          nodeCount: data.nodes?.length ?? 'N/A', 
          edgeCount: data.links?.length ?? 'N/A' 
        });
      } catch (err) {
        console.error("Failed to fetch graph stats:", err);
        setGraphStats({ nodeCount: 'Err', edgeCount: 'Err'});
        // Optional: toast.error("Failed to load graph stats.");
      } finally {
        setStatsLoading(false);
      }
    };
    fetchStats();
  }, []);

  const handlePopulateGraph = async () => {
    setIsPopulating(true);
    setPopulateStatus('Starting population task...');
    toast.info("Requesting graph population from database...");

    try {
      const response = await fetch(POPULATE_GRAPH_URL, { method: 'POST' });
      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || `HTTP error! status: ${response.status}`);
      }
      
      setPopulateStatus(`Background task started successfully. Refresh stats or view graph later.`);
      toast.success(result.message || "Population task started!");
      // Maybe trigger a stats refresh after a delay?
      // setTimeout(() => fetchStats(), 10000); // Example: Refresh stats after 10s

    } catch (err) {
      console.error("Failed to trigger graph population:", err);
      setPopulateStatus(`Error starting task: ${err.message}`);
      toast.error(`Failed to start population: ${err.message}`);
    } finally {
      setIsPopulating(false);
      // Clear status message after a while?
      // setTimeout(() => setPopulateStatus(''), 15000);
    }
  };

  return (
    <Layout title="AI Knowledge Tools | SEER">
      <div className="space-y-8"> {/* Increased spacing */} 
        <div className="flex items-center space-x-3">
          <Library className="h-8 w-8 text-indigo-600" /> {/* Changed icon */} 
          <h1 className="text-3xl font-bold tracking-tight">AI Knowledge Tools</h1>
        </div>
        
        {/* Section 1: Manual Text Analysis */}
        <Card>
          <CardHeader>
             <CardTitle className='flex items-center'><Send className='mr-2 h-5 w-5'/> Analyze Text for Relationships</CardTitle>
             <CardDescription>Manually extract entities and relationships from unstructured text and add them directly to the knowledge graph.</CardDescription>
          </CardHeader>
          <CardContent>
            <ThreatTextAnalyzerCard /> { /* Reuse the existing component */ }
          </CardContent>
        </Card>

        {/* Section 2: Bulk Population */}
        <Card>
          <CardHeader>
            <CardTitle className='flex items-center'><DatabaseZap className='mr-2 h-5 w-5'/> Populate Graph from Database</CardTitle>
            <CardDescription>
              Scan existing structured data (Threats, Actors, Indicators, etc.) 
              in the database and build corresponding nodes and edges in the knowledge graph.
              This runs as a background task.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={handlePopulateGraph} disabled={isPopulating}>
              {isPopulating ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Starting Task...</>
              ) : (
                'Start Population Task'
              )}
            </Button>
            {populateStatus && (
              <p className={`mt-3 text-sm ${populateStatus.includes('Error') ? 'text-red-600' : 'text-muted-foreground'}`}>
                {populateStatus}
              </p>
            )}
          </CardContent>
        </Card>

        {/* Section 3: Graph Stats & Navigation */}
        <Card>
           <CardHeader>
             <CardTitle className='flex items-center'><Network className='mr-2 h-5 w-5'/> Knowledge Graph Overview</CardTitle>
             <CardDescription>Current status and link to the visual graph explorer.</CardDescription>
           </CardHeader>
           <CardContent className="flex flex-wrap justify-between items-center gap-4"> 
             <div className="flex items-center space-x-6">
                <div className="text-center">
                    <p className="text-sm text-muted-foreground">Nodes</p>
                    <p className="text-2xl font-bold">{statsLoading ? <Loader2 className="h-5 w-5 animate-spin inline" /> : graphStats.nodeCount}</p>
                </div>
                <div className="text-center">
                    <p className="text-sm text-muted-foreground">Edges</p>
                    <p className="text-2xl font-bold">{statsLoading ? <Loader2 className="h-5 w-5 animate-spin inline" /> : graphStats.edgeCount}</p>
                </div>
             </div>
             <Link href="/graph-explorer" passHref legacyBehavior>
                <Button variant="outline">View Graph Explorer</Button>
             </Link>
           </CardContent>
        </Card>

      </div>
    </Layout>
  );
} 