# Mock Data for SEER Threat Parser

This directory contains mock data files used for testing the SEER threat parser. These files simulate security-related content that would be crawled from the web.

## Template Structure

The `threat_template.json` file provides a template structure for creating new mock data files. Here's an explanation of each field:

- `job_id`: A unique identifier for the crawl job
- `url`: The source URL of the security content
- `status`: The status of the crawl job (usually "completed")
- `results`: An array of crawled content items
  - `id`: Unique identifier for the result
  - `url`: URL of the specific content
  - `title`: Title of the security incident or vulnerability
  - `content`: The main text content containing threat information
  - `content_type`: Format of the content (usually "text/plain")
  - `metadata`: Additional information about the content
    - `timestamp`: When the content was published or discovered
    - `source_type`: Type of source (blog, forum, etc.)
    - `extracted_iocs`: Indicators of compromise
      - `cves`: CVE identifiers related to the threat
      - `protocols`: Network protocols involved
      - `attack_patterns`: Techniques used by attackers
      - `malware_families`: Types of malware mentioned
      - `affected_software`: Software affected by the threat

## Creating New Mock Data

To create a new mock threat for testing:

1. Copy `threat_template.json` to a new file (e.g., `mock_crawl_6.json`)
2. Fill in the fields with realistic security information
3. Ensure the content field contains detailed information about the threat
4. Include specific technical details that the parser should extract

## Using Mock Data for Testing

You can use these mock data files to test the SEER parser by:

1. Submitting them via the Dashboard's Parser page
2. Using them in automated tests
3. Directly processing them via the API endpoint `/api/parse`

The parser will extract structured threat intelligence from the content and save it to the database.

## Examples

See the existing mock_crawl_*.json files for examples of different threat types:

- `mock_crawl_5.json`: Log4Shell vulnerability (CVE-2021-44228)
- `mock_crawl_4.json`: Example of a different threat
- And so on...

When creating new mock data, try to vary the threat types, severities, and technical details to test the parser's capabilities. 