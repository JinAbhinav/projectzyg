import React, { useState, useEffect } from 'react';
// Remove dynamic import
// import dynamic from 'next/dynamic'; 
import { Layout } from '../components/layout/layout'; // Adjust path if needed
// Use static import again
import ForceGraph2D from 'react-force-graph-2d';
import { Loader2 } from 'lucide-react';

// Remove dynamic component definition
// const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), {
//   ssr: false,
//   loading: () => <div className="flex-grow flex items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" /><span className="ml-2">Loading Graph Component...</span></div>
// });

// Assuming this endpoint exists and returns { nodes: [], links: [] }
const GRAPH_DATA_URL = '/api/graph/data';

export default function GraphExplorerPage() {
  // Keep state for raw graph data, loading, and error
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  // Remove state for cytoscape formatted elements
  // const [cytoscapeElements, setCytoscapeElements] = useState([]); 

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetch(GRAPH_DATA_URL);
        if (!response.ok) {
          // Improved error message handling
          let errorMsg = `HTTP error! status: ${response.status}`;
          try {
            const errorData = await response.json();
            errorMsg = errorData.detail || errorMsg; // Use detail from FastAPI error if available
          } catch (jsonError) { /* Ignore if response is not JSON */ }
          throw new Error(errorMsg);
        }
        const data = await response.json();
        
        // Basic validation of returned structure
        if (!data || !Array.isArray(data.nodes) || !Array.isArray(data.links)) {
           console.error("Invalid data structure received from API:", data);
           throw new Error('Invalid data structure received from API.');
        }

        setGraphData(data); // Set the data directly { nodes: [], links: [] }

      } catch (err) {
        console.error("Failed to fetch graph data:", err);
        setError(err.message || 'Failed to load graph data.');
        setGraphData({ nodes: [], links: [] }); // Clear data on error
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  // Remove Cytoscape layout and stylesheet constants
  // const layout = { ... };
  // const stylesheet = [ ... ];

  // Custom node rendering (optional, but useful for styling)
  const nodeCanvasObject = (node, ctx, globalScale) => {
    const label = node.value || node.id;
    const fontSize = 12 / globalScale;
    ctx.font = `${fontSize}px Sans-Serif`;
    const textWidth = ctx.measureText(label).width;
    const nodeSize = 5; // Base node size

    // Simple color mapping (can be expanded)
    let color = '#666'; // Default grey
    if (node.type === 'ThreatActor') color = '#dc2626'; // Red
    else if (node.type === 'Malware') color = '#ea580c'; // Orange
    else if (node.type === 'Indicator') color = '#ca8a04'; // Yellow
    else if (node.type === 'Vulnerability') color = '#65a30d'; // Lime
    else if (node.type === 'Threat') color = '#4f46e5'; // Indigo
    
    // Draw circle for node
    ctx.beginPath();
    ctx.arc(node.x, node.y, nodeSize, 0, 2 * Math.PI, false);
    ctx.fillStyle = color;
    ctx.fill();

    // Draw label
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#333'; // Label color
    ctx.fillText(label, node.x, node.y + nodeSize + fontSize * 0.5);
  };

  // Check if window is defined (basic client-side check)
  // This helps prevent SSR errors but dynamic import is the standard way
  const [isClient, setIsClient] = useState(false);
  useEffect(() => {
    setIsClient(true);
  }, []);

  return (
    <Layout title="Knowledge Graph Explorer | SEER">
      {/* Ensure parent div has explicit height for react-force-graph */}
      <div className="flex flex-col h-[calc(100vh-4rem)]"> {/* Adjusted height calculation using 4rem (64px) as default */}
        <h1 className="text-3xl font-bold tracking-tight mb-4 px-4 pt-4">Knowledge Graph Explorer</h1>
        
        {isLoading && (
          <div className="flex-grow flex items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            <span className="ml-2">Loading graph data...</span>
          </div>
        )}
        {error && (
          <div className="flex-grow flex items-center justify-center text-red-600">
            Error loading graph: {error}
          </div>
        )}
        {!isLoading && !error && (
          <div className="flex-grow border rounded-lg overflow-hidden bg-gray-50 shadow relative"> {/* Added relative for potential absolute positioned elements inside graph */}
            {/* Only render ForceGraph2D on the client side */} 
            {isClient && graphData.nodes.length > 0 ? (
              <ForceGraph2D
                graphData={graphData} // Use the fetched data directly
                nodeLabel="value" // Show node value on hover
                linkLabel="type" // Show relationship type on link hover
                nodeCanvasObject={nodeCanvasObject} // Custom node rendering
                nodeRelSize={5} // Base node size used in canvas object
                linkDirectionalArrowLength={3.5}
                linkDirectionalArrowRelPos={1}
                linkCurvature={0.1}
                width={undefined} // Let container define width
                height={undefined} // Let container define height - requires container to have height!
                // Consider adding interaction handlers: 
                // onNodeClick={handleNodeClick} 
                // onLinkClick={handleLinkClick}
              />
            ) : (
               !isClient ? 
               <div className="flex items-center justify-center h-full text-muted-foreground">Initializing graph...</div> :
               <div className="flex items-center justify-center h-full text-muted-foreground">
                 No graph data available to display. Try populating the graph first.
              </div>
            )}
          </div>
        )}
      </div>
    </Layout>
  );
} 