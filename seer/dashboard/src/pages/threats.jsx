import React, { useState, useEffect } from 'react';
import { Layout } from '../components/layout/layout';
import { Button } from '../components/ui/button';
import { AlertTriangle, Search, Calendar, Zap, Target, Shield, ChevronRight, Loader2, BarChart } from 'lucide-react';
import { truncate, getSeverityColor } from '../lib/utils';
import { getThreats } from '../lib/threat-service';

export default function ThreatsPage() {
  const [threats, setThreats] = useState([]);
  const [selectedThreat, setSelectedThreat] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterSeverity, setFilterSeverity] = useState('ALL');
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);

    const loadThreats = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const fetchedThreats = await getThreats();
        setThreats(fetchedThreats);
      } catch (err) {
        console.error("Failed to load threats:", err);
        setError(err.message || 'Failed to load threats.');
      } finally {
        setIsLoading(false);
      }
    };

    loadThreats();
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
                          <div className="font-medium">{threat.title || threat.category || 'Untitled Threat'}</div>
                          <div className="text-xs text-muted-foreground mt-1">
                            {threat.created_at}
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
                        <h2 className="text-2xl font-bold">{selectedThreat.title || selectedThreat.category}</h2>
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
                          {selectedThreat.created_at}
                        </p>
                      </div>
                      <div className="rounded-md bg-muted p-4">
                        <div className="flex items-center mb-2">
                          <Search className="h-4 w-4 mr-2 text-muted-foreground" />
                          <h4 className="font-medium">Source</h4>
                        </div>
                        <p className="text-sm truncate">
                          {selectedThreat.source_url || 'N/A'}
                        </p>
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium mb-2 flex items-center">
                        <Zap className="h-4 w-4 mr-2 text-yellow-500" />
                        Description/Justification
                      </h4>
                      <p className="text-sm">
                        {selectedThreat.description || selectedThreat.justification || 'No details available.'}
                      </p>
                    </div>

                    {selectedThreat.potential_targets && selectedThreat.potential_targets.length > 0 && (
                      <div>
                        <h4 className="font-medium mb-2 flex items-center">
                          <Target className="h-4 w-4 mr-2 text-red-500" />
                          Potential Targets
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {selectedThreat.potential_targets?.map((target, idx) => (
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