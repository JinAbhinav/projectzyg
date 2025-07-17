import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { Layout } from '../components/layout/layout';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import { Loader2, Server, Network, Globe, AlertTriangle, CalendarDays, ShieldCheck, Info, Search } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API_BASE_URL = 'http://localhost:8000/api';

const fetchShodanHostDetails = async (ipAddress) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/v1/enrich/shodan/ip/${ipAddress}`);
    if (response.data.error) {
      // The backend endpoint now returns a structure with an error field for graceful handling
      throw new Error(response.data.error);
    }
    return response.data;
  } catch (error) {
    console.error(`Error fetching Shodan host details for ${ipAddress}:`, error);
    throw error; // Re-throw to be caught by the calling function
  }
};

export default function HostExplorerPage() {
  const router = useRouter();
  const { ip } = router.query; // Get IP from URL query parameter

  const [shodanData, setShodanData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [inputIp, setInputIp] = useState(ip || ''); // For the input field

  useEffect(() => {
    if (ip) {
      setInputIp(ip); // Sync input field if IP from URL changes
      const loadData = async () => {
        setIsLoading(true);
        setError(null);
        setShodanData(null);
        try {
          const data = await fetchShodanHostDetails(ip);
          setShodanData(data);
        } catch (err) {
          setError(err.message || `Failed to fetch Shodan data for ${ip}.`);
          toast.error(err.message || `Failed to fetch Shodan data for ${ip}.`);
        }
        setIsLoading(false);
      };
      loadData();
    }
  }, [ip]); // Re-run if IP from URL query changes

  const handleSearch = (e) => {
    e.preventDefault();
    if (inputIp && inputIp !== ip) {
      router.push(`/host-explorer?ip=${inputIp}`);
    }
  };

  const renderServiceDetails = (service) => (
    <div key={`${service.port}/${service.transport}`} className="p-3 bg-secondary/50 rounded-md text-sm mb-2">
      <p className="font-semibold">Port: {service.port}/{service.transport}</p>
      {service.banner && (
        <pre className="mt-1 p-2 bg-background/70 rounded text-xs whitespace-pre-wrap break-all overflow-auto max-h-40">
          {service.banner}
        </pre>
      )}
    </div>
  );

  return (
    <Layout title={`Host Explorer: ${ip || 'Search'} | SEER`}>
      <div className="space-y-6">
        <div className="flex flex-col md:flex-row justify-between md:items-center gap-4">
          <h1 className="text-3xl font-bold tracking-tight">Shodan Host Explorer</h1>
          <form onSubmit={handleSearch} className="flex gap-2 w-full md:w-auto">
            <Input 
              type="text"
              placeholder="Enter IP Address (e.g., 1.1.1.1)"
              value={inputIp}
              onChange={(e) => setInputIp(e.target.value)}
              className="min-w-[250px]"
            />
            <Button type="submit" disabled={isLoading || !inputIp || inputIp === ip}>
              <Search className="mr-2 h-4 w-4" /> Search
            </Button>
          </form>
        </div>

        {isLoading && (
          <div className="flex justify-center items-center py-10">
            <Loader2 className="h-12 w-12 animate-spin text-primary" />
          </div>
        )}

        {error && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Error Fetching Shodan Data</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {shodanData && !error && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Server className="mr-3 h-6 w-6 text-primary" /> IP: {shodanData.ip_str}
                </CardTitle>
                <CardDescription>
                  General information about this host as reported by Shodan.
                </CardDescription>
              </CardHeader>
              <CardContent className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-4 text-sm">
                <div><strong>Hostnames:</strong> {shodanData.hostnames?.join(', ') || 'N/A'}</div>
                <div><strong>Domains:</strong> {shodanData.domains?.join(', ') || 'N/A'}</div>
                <div><strong>Organization:</strong> {shodanData.org || 'N/A'}</div>
                <div><strong>ISP:</strong> {shodanData.isp || 'N/A'}</div>
                <div><strong>ASN:</strong> {shodanData.asn || 'N/A'}</div>
                <div className="flex items-center"><strong>Country:</strong> 
                  <span className="ml-1.5">{shodanData.country_name || 'N/A'}</span> 
                  {shodanData.country_code && 
                    <img src={`https://flagsapi.com/${shodanData.country_code}/flat/24.png`} alt={shodanData.country_code} className="inline h-4 ml-2" onError={(e) => e.target.style.display='none'} />
                  }
                </div>
                <div><strong>City:</strong> {shodanData.city || 'N/A'}</div>
                <div className="flex items-center"><strong>Last Update:</strong> 
                  <CalendarDays className="h-4 w-4 text-muted-foreground mx-1.5" /> 
                  {shodanData.last_update ? new Date(shodanData.last_update).toLocaleString() : 'N/A'}
                </div>
              </CardContent>
            </Card>

            {shodanData.ports && shodanData.ports.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Network className="mr-3 h-6 w-6 text-primary" /> Open Ports & Services
                  </CardTitle>
                  <CardDescription>
                    List of open ports and detected services with banners.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="mb-2 text-sm"><strong>Detected Open Ports:</strong> {shodanData.ports.join(', ')}</p>
                  {shodanData.services && shodanData.services.length > 0 ? (
                    <div className="max-h-[400px] overflow-y-auto pr-2">
                      {shodanData.services.map(renderServiceDetails)}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No detailed service information available.</p>
                  )}
                </CardContent>
              </Card>
            )}

            {shodanData.vulnerabilities && shodanData.vulnerabilities.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <ShieldCheck className="mr-3 h-6 w-6 text-red-500" /> Known Vulnerabilities (CVEs)
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="list-disc list-inside space-y-1 text-sm">
                    {shodanData.vulnerabilities.map(vuln => <li key={vuln}>{vuln}</li>)}
                  </ul>
                </CardContent>
              </Card>
            )}

            {!shodanData.ports?.length && !shodanData.vulnerabilities?.length && (
                 <Alert>
                    <Info className="h-4 w-4" />
                    <AlertTitle>Limited Information</AlertTitle>
                    <AlertDescription>Shodan has limited information for this IP address, or it may not have open ports or known vulnerabilities listed.</AlertDescription>
                </Alert>
            )}
          </div>
        )}
      </div>
    </Layout>
  );
} 