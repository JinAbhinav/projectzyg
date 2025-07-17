# Crawl Result for Job ID: 1746638230

**URL:** https://www.reddit.com/r/threatintel/comments/1kh2cpw/diamorphine_rootkit_deploys_crypto_miner_on_linux/

**Status:** completed

## Full JSON Output

```json
{
    "job_id": "1746638230",
    "url": "https://www.reddit.com/r/threatintel/comments/1kh2cpw/diamorphine_rootkit_deploys_crypto_miner_on_linux/",
    "status": "completed",
    "results": [
        {
            "id": 1,
            "url": "https://www.reddit.com/r/threatintel/comments/1kh2cpw/diamorphine_rootkit_deploys_crypto_miner_on_linux/",
            "title": "Reddit - The heart of the internet",
            "content": "Go to threatintel\nr/threatintel\nr/threatintel\nSharing of information about threats, vulnerabilities, tools and trends across the security industry.\nMembers\nOnline\n\u2022\nANYRUN-team\nDiamorphine rootkit deploys crypto miner on Linux\nA forked script is used to stealthily deploy a cryptocurrency miner, disguised as a Python file. Diamorphine intercepts system calls and hides its presence. Let\u2019s take a closer look at this threat\u2019s behavior using ANYRUN\u2019s Linux VM, which provides full visibility into process activity and persistence mechanisms.\nThe attack script capabilities:\nPropagating from the compromised host to other systems, including stealing SSH keys to move laterally\nPrivilege escalation\nInstalling required dependencies\nEstablishing persistence via systemd\nTerminating rival cryptocurrency miners\nEstablishing a three\u2011layer self\u2011defense stack: replacing the\u202fps\u202futility, installing the Diamorphine rootkit, loading a library that intercepts system calls\nBoth the rootkit and the miner are built from open\u2011source code obtained on GitHub, highlighting the ongoing abuse of publicly available tooling in Linux threats.\nSee Linux analysis session and collect IOCs:\nhttps://app.any.run/tasks/a750fe79-9565-449d-afa3-7e523f84c6ad/\nUse this TI Lookup query to find fresh samples and enhance your organization's security response:\nhttps://intelligence.any.run/analysis/lookup\nRead more",
            "content_type": "text/plain",
            "metadata": {
                "timestamp": "2025-05-07T17:17:11+00:00Z",
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
