# Crawl Result for Job ID: 1746640650

**URL:** https://github.com/offensive-hub/black-widow

**Status:** completed

## Full JSON Output

```json
{
    "job_id": "1746640650",
    "url": "https://github.com/offensive-hub/black-widow",
    "status": "completed",
    "results": [
        {
            "id": 1,
            "url": "https://github.com/offensive-hub/black-widow",
            "title": "GitHub - offensive-hub/black-widow: GUI based offensive penetration testing tool (Open Source)",
            "content": "description\nblack-widow is one of the most useful, powerful and complete offensive penetration testing tool\nblack-widow\nOffensive penetration testing tool (Open Source)\nblack-widow provides easy ways to execute many kinds of information gatherings and attacks.\nFully Open Source\nWritten in Python\nContinuously updated and extended\nFeatures\nLocalhost Web GUI\nSniffing\nWebsite crawling\nWeb page parsing\nSQL injection\nInjected database management\nBrute force attacks\nCluster between other black-widows\nMultiple asynchronous requests\nMultiple targets management\nUseful CTF features\nAPT installation (ubutu/debian)\nsudo add-apt-repository ppa:offensive-hub/black-widow\nsudo apt-get update\nsudo apt-get install black-widow\nAPT installation (other distro)\nPut the following text on\n/etc/apt/sources.list.d/black-widow.list\nfile:\ndeb http://ppa.launchpad.net/offensive-hub/black-widow/ubuntu focal main \ndeb-src http://ppa.launchpad.net/offensive-hub/black-widow/ubuntu focal main\nExecute the following commands:\nsudo sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 5D26C76613E84EA9\nsudo apt-get update\nsudo apt-get install black-widow\nPyPI installation\nsudo pip3 install black-widow\nDocker installation\nIf you haven't Docker,\ninstall it\nGUI:\ndocker run -d -p 8095:80 offensive/black-widow -g\nThan visit:\nhttp://localhost:8095\nCommand line:\ndocker run --rm offensive/black-widow <arguments>\nManual installation\nsudo apt-get update && sudo apt-get install tidy clang tshark\nmkdir black-widow\ncd black-widow\ntouch black-widow.py && chmod +x black-widow.py\nCopy and paste the following code in file\nblack-widow.py\n:\n#!/usr/bin/env python3\nfrom\nblack_widow\n.\nblack_widow\nimport\nmain\nif\n__name__\n==\n\"__main__\"\n:\nmain\n()\ngit clone git@github.com:offensive-hub/black-widow.git black_widow\nsudo pip3 install -U -r black_widow/requirements.txt\n./black-widow.py --django migrate black_widow\nNow you can run\nblack-widow\nwith:\n./black-widow.py <arguments>\nRun\nGUI:\nblack-widow -g\nCommand line:\nblack-widow <arguments>\nDebug\nRun django (examples):\nblack-widow --django runserver\nblack-widow --django help\nblack-widow --django \"help createsuperuser\"\nProject layout\n[root]\n  |\n  |-- app/              # Main application package\n  |    |\n  |    |-- arguments/       # User input arguments parser (100%)\n  |    |\n  |    |-- attack/          # Attack modality package (0%)\n  |    |-- defense/         # Defense modality package (0%)\n  |    |\n  |    |-- gui/             # Graphical User Interface package (100%)\n  |    |\n  |    |-- helpers/         # Helper methods package (100%)\n  |    |\n  |    |-- managers/        # Managers package\n  |    |    |\n  |    |    |-- cluster/        # Cluster managers package (0%)\n  |    |    |-- crypto/         # Encryption managers package (70%)\n  |    |    |-- injection/      # Injection managers package (60%)\n  |    |    |-- parser/         # Parser managers package (100%)\n  |    |    |-- request/        # Request managers package (70%)\n  |    |    |-- sniffer/        # Sniffer managers package (95%)\n  |    |\n  |    |-- services/        # Services package\n  |    |    |\n  |    |    |-- logger.py       # Logger service (100%)\n  |    |    |-- multitask.py    # MultiTask service (100%)\n  |    |    |-- serializer.py   # PickleSerializer and JsonSerializer serivces (100%)\n  |    |\n  |    |-- storage/         # Storage directory\n  |    |\n  |    |-- env.py           # Environment variables management\n  |\n  |-- .env              # Environment variables\n  |\n  |-- black-widow.py    # Main executable\nLinks\nHomepage:\nhttps://black-widow.it\nPyPI:\nhttps://pypi.org/project/black-widow\nGitHub:\nhttps://github.com/offensive-hub/black-widow\nDocker Registry:\nhttps://hub.docker.com/r/offensive/black-widow\nPPA:\nLaunchpad.net\nFree Software Directory:\nhttps://directory.fsf.org/wiki/Black-widow\nContacts\nfabrizio@fubelli.org\nAuthors\nFabrizio Fubelli\nThanks to\nPyShark\nSqlmap\nMaterial Dashboard\nFollow Us\nSPONSORS\n1st level Sponsors\n2nd level Sponsors\n3th level Sponsors",
            "content_type": "text/plain",
            "metadata": {
                "timestamp": "2025-05-07T17:57:31+00:00Z",
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
