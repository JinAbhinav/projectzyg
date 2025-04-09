import React, { useState, useEffect } from 'react';
import { Layout } from '../components/layout/layout';
import { Button } from '../components/ui/button';
import { AlertTriangle, Search, Calendar, Zap, Target, Shield, ChevronRight, Loader2, BarChart } from 'lucide-react';
import { truncate, getSeverityColor, getSeverityTextColor } from '../lib/utils';

// Mock data for threats
const mockThreats = [
  {
    id: 1,
    category: 'Zero-day Exploit',
    severity: 'CRITICAL',
    confidence: 92.5,
    potential_targets: ['Windows Server', 'Enterprise Networks'],
    justification: 'The text explicitly mentions a zero-day vulnerability for Windows Server 2022 with remote code execution capabilities. This represents a critical threat as it has not been patched and affects enterprise server infrastructure.',
    created_at: '2023-11-05T10:23:15Z',
    crawl_result: {
      id: 101,
      url: 'https://darkforum.example.com/threads/new-zero-day',
      title: 'New Zero-Day Exploit Discussion',
    }
  },
  {
    id: 2,
    category: 'Ransomware',
    severity: 'HIGH',
    confidence: 88.0,
    potential_targets: ['Finance', 'Healthcare', 'Education'],
    justification: 'The content directly refers to ransomware-as-a-service with a focus on high-value sectors including finance, healthcare, and education. The organized nature and affiliate model indicates sophisticated actors.',
    created_at: '2023-11-04T14:45:22Z',
    crawl_result: {
      id: 102,
      url: 'https://darkforum.example.com/threads/ransomware-attack',
      title: 'Upcoming Ransomware Campaign',
    }
  },
  {
    id: 3,
    category: 'Data Breach',
    severity: 'HIGH',
    confidence: 95.0,
    potential_targets: ['Tech Company', 'Employees', 'Customers'],
    justification: 'The text indicates a major data breach of a Fortune 500 tech company, with sensitive employee and customer data exposed, including emails, passwords, and personal information.',
    created_at: '2023-11-03T08:12:44Z',
    crawl_result: {
      id: 301,
      url: 'https://leaksite.example.net/dumps/tech-company-breach',
      title: 'Corporate Database Dump - Fortune 500 Company',
    }
  },
  {
    id: 4,
    category: 'DDoS',
    severity: 'MEDIUM',
    confidence: 80.0,
    potential_targets: ['Government Websites'],
    justification: 'The content describes coordination of DDoS attacks specifically targeting government websites, suggesting hacktivist or politically motivated activity.',
    created_at: '2023-11-02T19:34:55Z',
    crawl_result: {
      id: 401,
      url: 'https://telegram.example.org/channel/cyberthreats',
      title: 'DDoS Attack Coordination',
    }
  },
  {
    id: 5,
    category: 'Credential Theft',
    severity: 'HIGH',
    confidence: 85.0,
    potential_targets: ['Cloud Services', 'Development Teams'],
    justification: 'The post offers stolen API keys and access tokens for major cloud platforms including AWS, Azure, and GCP. This indicates a serious security breach that could lead to unauthorized access to cloud resources.',
    created_at: '2023-11-01T12:22:33Z',
    crawl_result: {
      id: 501,
      url: 'https://pasteboard.example.io/paste123',
      title: 'Stolen API Keys',
    }
  },
];

export default function ThreatsPage() {
  const [threats, setThreats] = useState([]);
  const [selectedThreat, setSelectedThreat] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [filterSeverity, setFilterSeverity] = useState('ALL');

  // In a real implementation, you would fetch data from the API here
  useEffect(() => {
    setIsLoading(true);
    
    // Simulate API delay
    const timer = setTimeout(() => {
      setThreats(mockThreats);
      setIsLoading(false);
    }, 500);
    
    return () => clearTimeout(timer);
  }, []);

  const filteredThreats = filterSeverity === 'ALL' 
    ? threats 
    : threats.filter(threat => threat.severity === filterSeverity);

  return (
    <Layout title="Threats | SEER">
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h1 className="text-3xl font-bold tracking-tight">Threat Analysis</h1>
          <div className="flex items-center gap-2">
            <select 
              className="rounded-md border-input bg-background px-3 py-1 text-sm ring-offset-background"
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value)}
            >
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
            <Button>
              <BarChart className="mr-2 h-4 w-4" />
              Threat Report
            </Button>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          <div className="md:col-span-1 space-y-4">
            <div className="rounded-lg border bg-card text-card-foreground shadow-sm">
              <div className="p-4 border-b flex justify-between items-center">
                <h3 className="text-lg font-medium">Threats</h3>
                <span className="text-sm text-muted-foreground">
                  {filteredThreats.length} found
                </span>
              </div>
              <div className="divide-y max-h-[600px] overflow-y-auto">
                {isLoading ? (
                  <div className="p-8 flex justify-center">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                  </div>
                ) : filteredThreats.length === 0 ? (
                  <div className="p-6 text-center text-muted-foreground">
                    No threats found
                  </div>
                ) : (
                  filteredThreats.map((threat) => (
                    <div 
                      key={threat.id} 
                      className={`p-4 hover:bg-muted/50 cursor-pointer transition-colors ${
                        selectedThreat?.id === threat.id ? 'bg-muted' : ''
                      }`}
                      onClick={() => setSelectedThreat(threat)}
                    >
                      <div className="flex justify-between items-start">
                        <div className="max-w-[70%]">
                          <div className="font-medium">{threat.category}</div>
                          <div className="text-xs text-muted-foreground mt-1">
                            {new Date(threat.created_at).toLocaleString()}
                          </div>
                        </div>
                        <div className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(threat.severity)}`}>
                          {threat.severity}
                        </div>
                      </div>
                      <div className="mt-2 text-xs text-muted-foreground">
                        {truncate(threat.justification, 70)}
                      </div>
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
                  {selectedThreat ? `Threat Details` : 'Select a Threat'}
                </h3>
              </div>
              <div className="p-4">
                {!selectedThreat ? (
                  <div className="text-center py-12 text-muted-foreground">
                    Select a threat to view details
                  </div>
                ) : (
                  <div className="space-y-6">
                    <div className="flex flex-col sm:flex-row justify-between">
                      <div>
                        <h2 className="text-2xl font-bold">{selectedThreat.category}</h2>
                        <div className="flex items-center mt-2">
                          <div className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(selectedThreat.severity)}`}>
                            {selectedThreat.severity}
                          </div>
                          <div className="text-sm text-muted-foreground ml-2">
                            Confidence: <span className="font-medium">{selectedThreat.confidence}%</span>
                          </div>
                        </div>
                      </div>
                      <div className="mt-4 sm:mt-0">
                        <Button variant="outline" size="sm">
                          <Shield className="mr-2 h-4 w-4" />
                          Generate Alert
                        </Button>
                      </div>
                    </div>

                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="rounded-md bg-muted p-4">
                        <div className="flex items-center mb-2">
                          <Calendar className="h-4 w-4 mr-2 text-muted-foreground" />
                          <h4 className="font-medium">Detected</h4>
                        </div>
                        <p className="text-sm">
                          {new Date(selectedThreat.created_at).toLocaleString()}
                        </p>
                      </div>
                      <div className="rounded-md bg-muted p-4">
                        <div className="flex items-center mb-2">
                          <Search className="h-4 w-4 mr-2 text-muted-foreground" />
                          <h4 className="font-medium">Source</h4>
                        </div>
                        <p className="text-sm truncate">
                          {selectedThreat.crawl_result.url}
                        </p>
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium mb-2 flex items-center">
                        <Zap className="h-4 w-4 mr-2 text-yellow-500" />
                        Analysis
                      </h4>
                      <p className="text-sm">
                        {selectedThreat.justification}
                      </p>
                    </div>

                    {selectedThreat.potential_targets && selectedThreat.potential_targets.length > 0 && (
                      <div>
                        <h4 className="font-medium mb-2 flex items-center">
                          <Target className="h-4 w-4 mr-2 text-red-500" />
                          Potential Targets
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {selectedThreat.potential_targets.map((target, idx) => (
                            <div key={idx} className="bg-muted px-3 py-1 rounded-full text-xs">
                              {target}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="rounded-lg border p-4">
                      <h4 className="font-medium mb-3">Recommended Actions</h4>
                      <div className="space-y-3">
                        <div className="flex">
                          <ChevronRight className="h-5 w-5 mr-2 text-primary flex-shrink-0" />
                          <p className="text-sm">
                            {selectedThreat.severity === 'CRITICAL' 
                              ? 'Immediate action required. Isolate affected systems and deploy emergency patches.'
                              : selectedThreat.severity === 'HIGH'
                              ? 'Prioritize patching and monitoring of potentially affected systems.'
                              : 'Monitor systems and apply security updates as appropriate.'}
                          </p>
                        </div>
                        <div className="flex">
                          <ChevronRight className="h-5 w-5 mr-2 text-primary flex-shrink-0" />
                          <p className="text-sm">
                            Update threat intelligence feeds and security controls to detect this specific threat pattern.
                          </p>
                        </div>
                        <div className="flex">
                          <ChevronRight className="h-5 w-5 mr-2 text-primary flex-shrink-0" />
                          <p className="text-sm">
                            Brief security team on indicators of compromise and recommended mitigations.
                          </p>
                        </div>
                      </div>
                    </div>
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