import React from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Separator } from '../ui/separator';
import { getSeverityColor, formatDate, truncate } from '../../lib/utils';
import { JsonViewer } from '../ui/json-viewer';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { AlertTriangle, Check, List, Code, RefreshCw } from 'lucide-react';

export const ThreatResult = ({ threatData, isLoading = false }) => {
  if (isLoading) {
    return (
      <Card className="w-full mb-4">
        <CardHeader>
          <div className="flex items-center">
            <RefreshCw className="h-5 w-5 mr-2 animate-spin" />
            <CardTitle className="text-lg">Processing threat data...</CardTitle>
          </div>
          <CardDescription>The NLP/LLM parser is analyzing the content</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-40 flex items-center justify-center border rounded-md bg-gray-50">
            <p className="text-gray-500">Processing results will appear here</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!threatData || Object.keys(threatData).length === 0) {
    return (
      <Card className="w-full mb-4">
        <CardHeader>
          <CardTitle className="text-lg">No threat data available</CardTitle>
          <CardDescription>There is no threat information to display</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  // Destructure with defaults for optional fields to avoid null errors
  const {
    title = 'N/A',
    description = 'No description available.',
    threat_type = 'Unknown',
    severity = 'UNKNOWN',
    confidence = 0,
    source_url = '#',
    created_at = new Date().toISOString(),
    tactics = [], // Default to empty array
    techniques = [], // Default to empty array
    threat_actors = [], // Default to empty array
    indicators = [], // Default to empty array
    affected_systems = [], // Default to empty array
    mitigations = [], // Default to empty array
    references = [] // Default to empty array
  } = threatData || {}; // Ensure threatData itself is not null/undefined

  const formattedDate = new Date(created_at).toLocaleDateString('en-US', {
    year: 'numeric', month: 'long', day: 'numeric'
  });

  const severityClass = getSeverityColor(severity);
  const confidencePercent = confidence ? Math.round(confidence * 100) : 0;

  return (
    <Card className="w-full mb-4">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-xl">{title || 'Untitled Threat'}</CardTitle>
            <CardDescription className="mt-1">
              {source_url && (
                <span className="block mb-1 text-sm">
                  <span className="text-gray-500">Source:</span> {truncate(source_url, 60)}
                </span>
              )}
              {created_at && (
                <span className="text-sm text-gray-500">
                  Processed: {formattedDate}
                </span>
              )}
            </CardDescription>
          </div>
          <div className="flex flex-col items-end gap-2">
            {severity && (
              <Badge className={severityClass}>
                <AlertTriangle className="h-3 w-3 mr-1" />
                {severity}
              </Badge>
            )}
            {confidence && (
              <Badge variant="outline" className="bg-blue-50">
                <Check className="h-3 w-3 mr-1" />
                {confidencePercent}% Confidence
              </Badge>
            )}
            {threat_type && (
              <Badge variant="outline">
                {threat_type}
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid grid-cols-3 mb-4">
            <TabsTrigger value="overview">
              <List className="h-4 w-4 mr-2" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="indicators">
              <AlertTriangle className="h-4 w-4 mr-2" />
              Indicators
            </TabsTrigger>
            <TabsTrigger value="raw">
              <Code className="h-4 w-4 mr-2" />
              Raw Data
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="overview" className="space-y-4">
            {description && (
              <div>
                <h3 className="text-sm font-medium mb-2">Description</h3>
                <p className="text-sm text-gray-700">{description}</p>
              </div>
            )}
            
            <Separator />
            
            {tactics && tactics.length > 0 && (
              <div>
                <h3 className="text-sm font-medium mb-2">Tactics</h3>
                <div className="flex flex-wrap gap-2">
                  {tactics.map((tactic, index) => (
                    <Badge key={index} variant="outline" className="bg-amber-50">
                      {tactic}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
            
            {techniques && techniques.length > 0 && (
              <div>
                <h3 className="text-sm font-medium mb-2">Techniques</h3>
                <div className="flex flex-wrap gap-2">
                  {techniques.map((technique, index) => (
                    <Badge key={index} variant="outline" className="bg-blue-50">
                      {technique}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </TabsContent>
          
          <TabsContent value="indicators">
            {indicators && indicators.length > 0 ? (
              <div className="space-y-4">
                <h3 className="text-sm font-medium">Detected Indicators</h3>
                <div className="border rounded-md divide-y">
                  {indicators.map((indicator, index) => (
                    <div key={index} className="p-3 flex justify-between items-center">
                      <div>
                        <span className="font-medium text-sm">{indicator.value}</span>
                        <Badge className="ml-2" variant="outline">{indicator.type}</Badge>
                      </div>
                      <Badge variant="outline">
                        {Math.round(indicator.confidence * 100)}% confidence
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center p-6 text-gray-500">
                No indicators detected
              </div>
            )}
          </TabsContent>
          
          <TabsContent value="raw">
            <div className="border rounded-md overflow-hidden">
              <JsonViewer data={threatData} name="threatData" collapsed={1} />
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}; 