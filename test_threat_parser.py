#!/usr/bin/env python3
"""
Test script for the threat parser.
"""

import os
import json
import argparse
from dotenv import load_dotenv
from seer.nlp_engine.threat_parser import ThreatParser

# Load environment variables
load_dotenv()

# Sample threat content
SAMPLE_THREAT = """
Breaking Security Alert: New Ransomware Campaign Targeting Healthcare

A new ransomware variant named "MediLock" has been observed targeting healthcare providers across North America and Europe. 
Initial infection vectors include phishing emails with malicious attachments disguised as patient records or insurance claims.

The ransomware is believed to be operated by a group calling themselves "CyberSurgeons", who have previously targeted financial 
institutions. Upon infection, the ransomware encrypts all medical records and patient databases with a strong RSA-4096 algorithm 
and demands payment of 50 Bitcoin for decryption.

Technical indicators:
- SHA256: 8a9f1b9b2e3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5
- C2 servers: medicalrecords-recovery.net (185.212.x.x), decrypt-hospital-data.com (91.35.x.x)
- Email: recovery@medicrypt.cc

Affected systems include Windows Server 2016/2019 running legacy medical record software.

Mitigation steps:
1. Apply latest security patches
2. Block the C2 domains and IPs
3. Implement email filtering for .js and .vbs attachments
4. Verify offline backups are functioning properly
5. Monitor for suspicious authentication attempts

MediLock has been observed to disable Windows Defender and other security solutions before encryption.
"""

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test the threat parser")
    parser.add_argument("--input", "-i", help="Path to input file with threat content")
    parser.add_argument("--output", "-o", help="Path to output file for results")
    
    args = parser.parse_args()
    
    # Get threat content
    if args.input:
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                content = f.read()
            print(f"Read content from {args.input}")
        except Exception as e:
            print(f"ERROR: Failed to read input file: {e}")
            return
    else:
        print("Using sample threat content")
        content = SAMPLE_THREAT
    
    # Initialize parser
    parser = ThreatParser()
    
    # Parse the threat
    try:
        source_url = "https://example.com/threat-alert"
        threat_info = parser.extract_threat_info(content, source_url)
        
        if threat_info:
            print("\nExtracted Threat Information:")
            print(f"Title: {threat_info.title}")
            print(f"Type: {threat_info.threat_type}")
            print(f"Severity: {threat_info.severity}")
            print(f"Confidence: {threat_info.confidence:.2f}")
            
            # Check if Supabase is configured
            if parser.supabase:
                print("\nSaving to Supabase...")
                result = parser.save_threat_to_supabase(threat_info)
                if result:
                    print("Successfully saved to Supabase")
                else:
                    print("Failed to save to Supabase")
            else:
                print("\nSkipping Supabase save (not configured)")
            
            # Save to file if requested
            if args.output:
                try:
                    with open(args.output, "w", encoding="utf-8") as f:
                        # Convert to dict and format dates
                        threat_dict = threat_info.dict()
                        for key, value in threat_dict.items():
                            if hasattr(value, "isoformat"):
                                threat_dict[key] = value.isoformat()
                        
                        json.dump(threat_dict, f, indent=2)
                    print(f"Saved results to {args.output}")
                except Exception as e:
                    print(f"ERROR: Failed to save output file: {e}")
        else:
            print("No threat information found")
    
    except Exception as e:
        print(f"ERROR: Failed to extract threat information: {e}")

if __name__ == "__main__":
    main() 