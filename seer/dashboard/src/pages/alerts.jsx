import React, { useState, useEffect, useCallback } from 'react';
import { Layout } from '../components/layout/layout';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { PlusCircle, Edit, Trash2, AlertTriangle, Loader2 } from 'lucide-react';
import { Switch } from "../components/ui/switch";
import { getRules, createRule, updateRule, deleteRule, getHistory } from '../lib/alert-service';

// Remove mock data
// const mockAlertRules = [...];
const mockRecentAlerts = [
  { id: 101, timestamp: new Date(Date.now() - 3600000).toISOString(), ruleName: 'Critical Ransomware Alert', type: 'Threat Detected', severity: 'CRITICAL', summary: 'Ransomware note detected on DarkForumX' },
  { id: 102, timestamp: new Date(Date.now() - 7200000).toISOString(), ruleName: 'Log4Shell IOC Match', type: 'IOC Match', severity: 'HIGH', summary: 'CVE-2021-44228 mentioned on PasteSiteY' },
];

const RULE_TYPES = [
    { value: 'severity_confidence', label: 'Severity & Confidence Threshold' },
    { value: 'ioc_match', label: 'Indicator of Compromise (IOC) Match' },
    { value: 'network_anomaly', label: 'Network Anomaly Score' },
    { value: 'specific_threat', label: 'Specific Threat Type' },
];

const AVAILABLE_CHANNELS = ['Email', 'Slack', 'Webhook'];

// Initial state for a new rule form
const initialRuleFormState = {
  id: null, // Used for tracking edits
  name: '',
  type: RULE_TYPES[0].value,
  condition_config: {},
  channels: [],
  enabled: true,
};

// Helper function for severity badge classes
const getSeverityBadgeClasses = (severity) => {
  switch (severity?.toLowerCase()) {
    case 'critical':
      return 'border-red-500 text-red-700 dark:border-red-400 dark:text-red-300';
    case 'high': // Use yellow for high
      return 'border-yellow-500 text-yellow-700 dark:border-yellow-400 dark:text-yellow-300';
    case 'medium': // Use blue for medium
      return 'border-blue-500 text-blue-700 dark:border-blue-400 dark:text-blue-300';
    default: // low, info, or unknown
      return 'border-gray-500 text-gray-700 dark:border-gray-400 dark:text-gray-300';
  }
};

export default function AlertsPage() {
  const [alertRules, setAlertRules] = useState([]);
  const [alertHistory, setAlertHistory] = useState([]);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState(null);
  const [showRuleForm, setShowRuleForm] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [ruleForm, setRuleForm] = useState(initialRuleFormState);
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const fetchAlertRules = useCallback(async () => {
    console.log('[fetchAlertRules] Setting isLoading to true');
    setIsLoading(true);
    setError(null);
    try {
      console.log('[fetchAlertRules] Calling getRules()...');
      const rules = await getRules();
      console.log('[fetchAlertRules] getRules() succeeded, received:', rules);
      setAlertRules(rules);
    } catch (err) {
      console.error('[fetchAlertRules] getRules() failed:', err);
      setError(err.message || 'Failed to load alert rules.');
    } finally {
      console.log('[fetchAlertRules] Setting isLoading to false (finally block)');
      setIsLoading(false);
    }
  }, []);

  const fetchAlertHistory = useCallback(async () => {
    console.log('[fetchAlertHistory] Setting isHistoryLoading to true');
    setIsHistoryLoading(true);
    setHistoryError(null);
    try {
      console.log('[fetchAlertHistory] Calling getHistory()...');
      const history = await getHistory();
      console.log('[fetchAlertHistory] getHistory() succeeded, received:', history);
      setAlertHistory(history);
    } catch (err) {
      console.error('[fetchAlertHistory] getHistory() failed:', err);
      setHistoryError(err.message || 'Failed to load alert history.');
    } finally {
      console.log('[fetchAlertHistory] Setting isHistoryLoading to false (finally block)');
      setIsHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAlertRules();
    fetchAlertHistory();
  }, [fetchAlertRules, fetchAlertHistory]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setRuleForm(prev => ({ ...prev, [name]: value }));
  };

  const handleSelectChange = (name, value) => {
    setRuleForm(prev => ({ ...prev, [name]: value, condition_config: {} })); // Reset conditions on type change
  };

  const handleCheckboxChange = (channel, checked) => {
    setRuleForm(prev => ({
      ...prev,
      channels: checked
        ? [...prev.channels, channel]
        : prev.channels.filter(c => c !== channel),
    }));
  };

  const handleSwitchChange = (name, checked) => {
    setRuleForm(prev => ({ ...prev, [name]: checked }));
  };

  const handleConditionChange = (e) => {
    const { name, value } = e.target;
    setRuleForm(prev => ({
        ...prev,
        condition_config: {
            ...prev.condition_config,
            [name]: value
        }
    }));
  };

  const resetForm = () => {
    setRuleForm(initialRuleFormState);
    setShowRuleForm(false);
    setError(null);
  };

  const handleAddNewRule = () => {
      setRuleForm(initialRuleFormState);
      setShowRuleForm(true);
  };

  const handleEditRule = (rule) => {
    setRuleForm({ ...rule }); // Load existing rule data into form
    setShowRuleForm(true);
  };

  const handleSaveRule = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { id, ...dataToSave } = ruleForm; // Exclude id from payload
      if (id) { // Update existing rule
        await updateRule(id, dataToSave);
      } else { // Create new rule
        await createRule(dataToSave);
      }
      resetForm();
      await fetchAlertRules(); // Refresh list after save/update
    } catch (err) {
      setError(err.message || 'Failed to save rule.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteRule = async (ruleId) => {
    // Find the rule name for a more informative confirmation
    const ruleToDelete = alertRules.find(rule => rule.id === ruleId);
    const ruleName = ruleToDelete ? ruleToDelete.name : 'this rule'; // Use a fallback

    if (!window.confirm(`Are you sure you want to delete the rule "${ruleName}"?`)) return; // <-- Update this line
    setIsLoading(true);
    setError(null);
    try {
      await deleteRule(ruleId);
      await fetchAlertRules(); // Refresh list
    } catch (err) {
      setError(err.message || 'Failed to delete rule.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleEnable = async (rule) => {
    setIsLoading(true);
    setError(null);
    try {
        // Optimistic update UI first (optional)
        // setAlertRules(prev => prev.map(r => r.id === rule.id ? {...r, enabled: !r.enabled} : r));
        await updateRule(rule.id, { enabled: !rule.enabled });
        await fetchAlertRules(); // Re-fetch to confirm state
    } catch (err) {
        setError(err.message || 'Failed to toggle rule status.');
        // Optionally revert optimistic update here
        await fetchAlertRules(); // Re-fetch to revert UI on error
    } finally {
        setIsLoading(false);
    }
  };

  // --- Conditional Form Fields --- //
  const renderConditionFields = () => {
      const { type, condition_config } = ruleForm;
      switch (type) {
          case 'severity_confidence':
              return (
                  <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-1">
                          <Label htmlFor="condition_severity">Minimum Severity</Label>
                          <select
                              id="condition_severity"
                              name="severity"
                              value={condition_config.severity || ''}
                              onChange={handleConditionChange}
                              className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                          >
                              <option value="" disabled>Select severity...</option>
                              <option value="LOW">Low</option>
                              <option value="MEDIUM">Medium</option>
                              <option value="HIGH">High</option>
                              <option value="CRITICAL">Critical</option>
                          </select>
                      </div>
                       <div className="space-y-1">
                          <Label htmlFor="condition_confidence">Minimum Confidence</Label>
                          <Input
                              id="condition_confidence"
                              name="confidence"
                              type="number"
                              min="0" max="100"
                              placeholder="e.g., 75 (%)"
                              value={condition_config.confidence || ''}
                              onChange={handleConditionChange}
                          />
                       </div>
                  </div>
              );
          case 'ioc_match':
              return (
                  <div className="space-y-1">
                      <Label htmlFor="condition_ioc_value">IOC Value (Regex supported)</Label>
                      <Input
                          id="condition_ioc_value"
                          name="ioc_value"
                          placeholder="e.g., suspicious.exe or ^1\.2\.3\."
                          value={condition_config.ioc_value || ''}
                          onChange={handleConditionChange}
                      />
                  </div>
              );
           case 'network_anomaly':
                return (
                    <div className="space-y-1">
                        <Label htmlFor="condition_score_threshold">Min Anomaly Score (0-100)</Label>
                        <Input
                            id="condition_score_threshold"
                            name="score_threshold"
                            type="number"
                            min="0" max="100"
                            placeholder="e.g., 80"
                            value={condition_config.score_threshold || ''}
                            onChange={handleConditionChange}
                        />
                    </div>
                );
            case 'specific_threat':
                return (
                     <div className="space-y-1">
                        <Label htmlFor="condition_threat_name">Threat Name (e.g., Ransomware, Phishing)</Label>
                        <Input
                            id="condition_threat_name"
                            name="threat_name"
                            placeholder="e.g., Ransomware"
                            value={condition_config.threat_name || ''}
                            onChange={handleConditionChange}
                        />
                    </div>
                );
          default:
              return <p className="text-sm text-muted-foreground">Select a rule type to configure conditions.</p>;
      }
  };

  return (
    <Layout title="Alerts | SEER">
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold tracking-tight">Alert Engine</h1>
          <Button onClick={handleAddNewRule} disabled={isLoading}>
            <PlusCircle className="mr-2 h-4 w-4" />
            Add New Rule
          </Button>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
            <strong className="font-bold"><AlertTriangle className="inline mr-2 h-5 w-5"/></strong>
            <span className="block sm:inline">{error}</span>
          </div>
        )}

        {showRuleForm && (
          <Card>
            <CardHeader>
              <CardTitle>{ruleForm.id ? 'Edit' : 'Add New'} Alert Rule</CardTitle>
              <CardDescription>Configure conditions to trigger notifications.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
               <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-1">
                        <Label htmlFor="ruleName">Rule Name</Label>
                        <Input id="ruleName" name="name" placeholder="e.g., Critical Ransomware Detection" value={ruleForm.name} onChange={handleInputChange} />
                    </div>
                    <div className="space-y-1">
                        <Label htmlFor="ruleType">Rule Type</Label>
                        <select
                            id="ruleType"
                            name="type"
                            value={ruleForm.type}
                            onChange={handleInputChange}
                            className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                            {RULE_TYPES.map(typeOption => (
                                <option key={typeOption.value} value={typeOption.value}>{typeOption.label}</option>
                            ))}
                        </select>
                    </div>
                </div>

                <div>
                    <Label>Conditions</Label>
                    <div className="p-4 border rounded bg-muted/40 mt-1">
                        {renderConditionFields()}
                    </div>
                </div>

                <div>
                    <Label>Notification Channels</Label>
                    <div className="flex flex-wrap gap-4 mt-2">
                        {AVAILABLE_CHANNELS.map(channel => (
                            <div key={channel} className="flex items-center space-x-2">
                                <input
                                    type="checkbox"
                                    id={`channel-${channel}`}
                                    checked={ruleForm.channels.includes(channel)}
                                    onChange={(e) => handleCheckboxChange(channel, e.target.checked)}
                                    className="peer h-4 w-4 shrink-0 rounded-sm border border-primary ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground"
                                />
                                <label
                                    htmlFor={`channel-${channel}`}
                                    className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                                >
                                    {channel}
                                </label>
                            </div>
                        ))}
                    </div>
                </div>
                 <div className="flex items-center space-x-2 pt-2">
                    <Switch
                        id="ruleEnabled"
                        checked={ruleForm.enabled}
                        onCheckedChange={(checked) => handleSwitchChange('enabled', checked)}
                    />
                    <Label htmlFor="ruleEnabled">Enabled</Label>
                </div>
            </CardContent>
            <CardFooter className="flex justify-end space-x-2">
              <Button variant="outline" onClick={resetForm} disabled={isLoading}>Cancel</Button>
              <Button onClick={handleSaveRule} disabled={isLoading}>
                {isLoading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin"/> Saving...</> : 'Save Rule'}
              </Button>
            </CardFooter>
          </Card>
        )}

        {isLoading && !showRuleForm && (
          <div className="flex justify-center items-center py-4"><Loader2 className="mr-2 h-5 w-5 animate-spin"/></div>
        )}
        {!isLoading && alertRules.length === 0 && (
          <div className="text-center py-4 text-muted-foreground">No alert rules configured yet.</div>
        )}
        {!isLoading && alertRules.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 border">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r">Name</th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r">Type</th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r">Condition Summary</th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r">Channels</th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r">Status</th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {alertRules.map((rule) => (
                  <tr key={rule.id}>
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 border-r">{rule.name}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 border-r">{RULE_TYPES.find(t => t.value === rule.type)?.label || rule.type}</td>
                    <td className="px-4 py-3 text-sm text-gray-500 border-r">
                      {/* Simple summary based on type - can be improved */} 
                      {rule.type === 'severity_confidence' && `Severity >= ${rule.condition_config.severity || 'N/A'}, Confidence >= ${rule.condition_config.confidence || 'N/A'}%`}
                      {rule.type === 'ioc_match' && `Matches IOC: ${rule.condition_config.ioc_value || 'N/A'}`}
                      {rule.type === 'network_anomaly' && `Score >= ${rule.condition_config.score_threshold || 'N/A'}`}
                      {rule.type === 'specific_threat' && `Threat: ${rule.condition_config.threat_name || 'N/A'}`}
                     </td>
                    <td className="px-4 py-3 text-sm text-gray-500 border-r">
                      {rule.channels.map(ch => <Badge key={ch} variant="secondary" className="mr-1 mb-1">{ch}</Badge>)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm border-r">
                      {/* Use Switch for toggling directly in the table */} 
                       <Switch
                          checked={rule.enabled}
                          onCheckedChange={() => handleToggleEnable(rule)}
                          disabled={isLoading}
                          aria-label={rule.enabled ? 'Disable Rule' : 'Enable Rule'}
                       />
                     </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm space-x-1">
                      <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => handleEditRule(rule)} disabled={isLoading}>
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon" className="text-red-600 hover:text-red-700 h-7 w-7" onClick={() => handleDeleteRule(rule.id)} disabled={isLoading}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Recent Alerts Triggered Table (Still uses mock data) */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Alerts Triggered</CardTitle>
            <CardDescription>History of recently triggered alerts.</CardDescription>
          </CardHeader>
          <CardContent>
            {/* Loading and Error states for History Table */}
            {isHistoryLoading && (
                <div className="flex justify-center items-center py-4"><Loader2 className="mr-2 h-5 w-5 animate-spin"/> Loading history...</div>
            )}
            {historyError && (
              <div className="text-center py-4 text-red-600">Error loading history: {historyError}</div>
            )}
            {!isHistoryLoading && !historyError && (
              <div className="overflow-x-auto max-h-[600px]">
                <table className="min-w-full divide-y divide-gray-200 border">
                  <thead className="bg-gray-50">
                    <tr>
                      <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r">Timestamp</th>
                      <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r">Rule Name (Snapshot)</th>
                      <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r">Alert Type</th>
                      <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r">Severity</th>
                      <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Summary</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {/* Map over alertHistory state */}
                    {alertHistory.map((alert) => (
                      <tr key={alert.id}>
                        {/* Use fields from alertHistory */}
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 border-r">{isMounted ? new Date(alert.triggered_at).toLocaleString() : '...'}</td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 border-r">{alert.rule_name_snapshot || 'N/A'}</td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 border-r">{alert.alert_type || 'N/A'}</td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm border-r">
                          <Badge
                            variant="outline"
                            className={getSeverityBadgeClasses(alert.severity)} // <-- Update this line
                          >
                            {alert.severity}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500">{alert.summary || 'No summary provided'}</td>
                      </tr>
                    ))}
                    {/* Update empty state check */}
                    {alertHistory.length === 0 && (
                      <tr>
                        <td colSpan={5} className="px-4 py-4 text-center text-sm text-muted-foreground">No alert history found.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

      </div>
    </Layout>
  );
} 