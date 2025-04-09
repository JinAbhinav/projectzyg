import React, { useState, useEffect } from 'react';
import { Layout } from '../components/layout/layout';
import { Button } from '../components/ui/button';
import { Shield, AlertTriangle, Search, Activity, Zap } from 'lucide-react';
import { truncate, getSeverityColor } from '../lib/utils';

// Mock data for the dashboard
const mockThreatStats = {
  totalThreats: 24,
  criticalThreats: 5,
  highThreats: 8,
  mediumThreats: 7,
  lowThreats: 4,
};

const mockRecentThreats = [
  {
    id: 1,
    category: 'Zero-day Exploit',
    severity: 'CRITICAL',
    confidence: 92.5,
    justification: 'The text explicitly mentions a zero-day vulnerability for Windows Server 2022 with remote code execution capabilities.',
    createdAt: '2023-11-05T10:23:15Z',
  },
  {
    id: 2,
    category: 'Ransomware',
    severity: 'HIGH',
    confidence: 88.0,
    justification: 'The content directly refers to ransomware-as-a-service with a focus on high-value sectors.',
    createdAt: '2023-11-04T14:45:22Z',
  },
  {
    id: 3,
    category: 'Data Breach',
    severity: 'HIGH',
    confidence: 95.0,
    justification: 'The text indicates a major data breach of a Fortune 500 tech company, with sensitive data exposed.',
    createdAt: '2023-11-03T08:12:44Z',
  },
];

const StatsCard = ({ icon: Icon, title, value, className }) => (
  <div className="rounded-lg border bg-card text-card-foreground shadow-sm p-6">
    <div className="flex items-center justify-between space-y-0 pb-2">
      <h3 className="tracking-tight text-sm font-medium">{title}</h3>
      <Icon className={`h-4 w-4 ${className}`} />
    </div>
    <div className="text-2xl font-bold">{value}</div>
  </div>
);

export default function Dashboard() {
  const [threatStats, setThreatStats] = useState(mockThreatStats);
  const [recentThreats, setRecentThreats] = useState(mockRecentThreats);
  const [isLoading, setIsLoading] = useState(false);

  // In a real implementation, you would fetch data from the API here
  useEffect(() => {
    // Simulating API call
    setIsLoading(true);
    
    // Simulate API delay
    const timer = setTimeout(() => {
      setThreatStats(mockThreatStats);
      setRecentThreats(mockRecentThreats);
      setIsLoading(false);
    }, 500);
    
    return () => clearTimeout(timer);
  }, []);

  return (
    <Layout title="Dashboard | SEER">
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <Button>
            <Zap className="mr-2 h-4 w-4" />
            Scan Now
          </Button>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StatsCard 
            icon={AlertTriangle} 
            title="Total Threats" 
            value={threatStats.totalThreats} 
            className="text-yellow-500"
          />
          <StatsCard 
            icon={AlertTriangle} 
            title="Critical Threats" 
            value={threatStats.criticalThreats} 
            className="text-red-500"
          />
          <StatsCard 
            icon={Search} 
            title="Crawl Jobs" 
            value="12" 
            className="text-blue-500"
          />
          <StatsCard 
            icon={Activity} 
            title="Prediction Accuracy" 
            value="92%" 
            className="text-green-500"
          />
        </div>

        <div className="rounded-lg border bg-card text-card-foreground shadow-sm">
          <div className="p-6 flex flex-col space-y-4">
            <h3 className="text-lg font-medium">Recent Threats</h3>
            <div className="divide-y">
              {recentThreats.map((threat) => (
                <div key={threat.id} className="py-4">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="flex items-center space-x-2">
                        <div className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(threat.severity)}`}>
                          {threat.severity}
                        </div>
                        <h4 className="font-medium">{threat.category}</h4>
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">
                        {truncate(threat.justification, 100)}
                      </p>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {new Date(threat.createdAt).toLocaleDateString()}
                    </div>
                  </div>
                  <div className="mt-2 flex items-center text-sm">
                    <span className="text-muted-foreground mr-2">Confidence:</span>
                    <div className="w-full max-w-24 bg-secondary rounded-full h-2">
                      <div 
                        className="bg-primary h-2 rounded-full" 
                        style={{ width: `${threat.confidence}%` }}
                      ></div>
                    </div>
                    <span className="ml-2 text-xs">{threat.confidence}%</span>
                  </div>
                </div>
              ))}
            </div>
            <Button variant="outline" className="mt-2 w-full">View All Threats</Button>
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
                Last updated: {new Date().toLocaleString()}
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
} 