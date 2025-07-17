# Crawl Result for Job ID: 1746695295

**URL:** https://www.reddit.com/r/threatintel/comments/1jlorfb/grandoreiro_attacks_latam/

**Status:** completed

## Full JSON Output

```json
{
    "job_id": "1746695295",
    "url": "https://www.reddit.com/r/threatintel/comments/1jlorfb/grandoreiro_attacks_latam/",
    "status": "completed",
    "results": [
        {
            "id": 1,
            "url": "https://www.reddit.com/r/threatintel/comments/1jlorfb/grandoreiro_attacks_latam/",
            "title": "Reddit - The heart of the internet",
            "content": "Go to threatintel\nr/threatintel\nr/threatintel\nSharing of information about threats, vulnerabilities, tools and trends across the security industry.\nMembers\nOnline\n\u2022\nANYRUN-team\nGrandoreiro attacks LATAM\nA phishing campaign is actively targeting Latin American countries, leveraging geofencing to filter victims. Behind it is Grandoreiro\u2014the most persistent banking trojan in LATAM.\nIt effectively bypasses many automated security solutions, making detection and response especially challenging but not for ANYRUN users.\nFull execution chain:\nhttps://app.any.run/tasks/02ea5d54-4060-4d51-9466-17983fc9f79e/\nMalware analysis:\nhttps://app.any.run/tasks/97141015-f97f-4ff0-b779-31307beafd47/\nThe execution chain begins with a phishing page luring users into downloading a fake PDF\u2014actually an archive delivering Grandoreiro.\nThe malware sends the victim\u2019s IP to ip-api to determine geolocation. Based on the result, it selects the appropriate C2 server.\nNext, it queries\ndns.google\nand provides the C&C domain name, which Google resolves to an IP address. This approach helps the malware avoid DNS-based blocking.\nFinally, the malware sends a GET request to obtain the resolved IP.\nActivity spiked between February 19 and March 14, and the campaign is still ongoing.\nThe campaign heavily relies on the subdomain contaboserver[.]net.\nUse these TI Lookup queries to find more IOCs, streamline investigations with actionable insights, and improve the efficiency of your organization's security response:\nhttps://intelligence.any.run/analysis/lookup\nhttps://intelligence.any.run/analysis/lookup\nRead more",
            "content_type": "text/plain",
            "metadata": {
                "timestamp": "2025-05-08T09:08:17+00:00Z",
                "source_type": "frontend_single_url",
                "extracted_iocs": {
                    "cves": [],
                    "protocols": [],
                    "attack_patterns": [],
                    "malware_families": [],
                    "affected_software": []
                }
            },
            "error": null
        }
    ]
}
```
