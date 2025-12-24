#!/usr/bin/env python3
"""
Complete Email Extraction Pipeline
===================================
End-to-end system that:
1. Takes company/firm name + person name
2. Finds the official website URL
3. Extracts the person's email from that website

Usage:
    python complete_email_extractor.py "Sullivan & Cromwell" "Robert Giuffra"
    python complete_email_extractor.py "DLA Piper" "New York" "John Smith"
"""

import os
import sys
import asyncio
import json
from typing import Optional, Dict
from dotenv import load_dotenv

# Import website finder
from website_finder_ai import website_selector

# Import email agent
from universal_email_agent_v5 import UniversalEmailAgent

load_dotenv()

# ============== LOGGING ==============

def log(level: str, msg: str, indent: int = 0):
    prefix = "   " * indent
    icons = {
        'start': '🚀', 'step': '📍', 'ok': '✅', 'fail': '❌', 'warn': '⚠️',
        'info': 'ℹ️', 'search': '🔍', 'found': '🎯', 'email': '📧'
    }
    print(f"{prefix}{icons.get(level, '•')} {msg}")

# ============== MAIN PIPELINE ==============

async def find_website_url(firm_name: str, address: str = "") -> Optional[str]:
    """Step 1: Find the official website URL"""
    log('step', f"STEP 1: Finding official website for '{firm_name}'")

    try:
        result = await website_selector(firm_name, address, debug=False)

        if result and result.get('best_url'):
            best_url = result['best_url']
            confidence = result.get('confidence', 0)
            reason = result.get('reason', '')

            log('found', f"Website found: {best_url}", 1)
            log('info', f"Confidence: {confidence:.0%} | Reason: {reason}", 1)

            # Try to find people/attorneys directory page
            people_urls = [
                f"{best_url.rstrip('/')}/people",
                f"{best_url.rstrip('/')}/attorneys",
                f"{best_url.rstrip('/')}/lawyers",
                f"{best_url.rstrip('/')}/professionals",
                f"{best_url.rstrip('/')}/team",
                f"{best_url.rstrip('/')}/our-people",
                f"{best_url.rstrip('/')}/leadership",
                best_url  # Fallback to homepage
            ]

            # Try to verify which directory page exists
            import requests
            for people_url in people_urls:
                try:
                    resp = requests.head(people_url, timeout=5, allow_redirects=True)
                    if resp.status_code == 200:
                        log('found', f"People directory: {people_url}", 1)
                        return people_url
                except:
                    continue

            # If no people directory found, use homepage
            log('warn', "No people directory found, using homepage", 1)
            return best_url
        else:
            log('fail', "Could not find official website", 1)
            return None

    except Exception as e:
        log('fail', f"Website finder error: {str(e)[:50]}", 1)
        return None

async def extract_email_from_url(url: str, person_name: str) -> Optional[Dict]:
    """Step 2: Extract email from the website"""
    log('step', f"STEP 2: Extracting email for '{person_name}' from website")

    try:
        agent = UniversalEmailAgent(url, person_name)
        result = await agent.run()
        return result
    except Exception as e:
        log('fail', f"Email extraction error: {str(e)[:50]}", 1)
        return None

async def complete_pipeline(firm_name: str, person_name: str, address: str = "") -> Dict:
    """Complete end-to-end pipeline"""

    print("=" * 70)
    log('start', "COMPLETE EMAIL EXTRACTION PIPELINE")
    print("=" * 70)
    log('info', f"Firm: {firm_name}")
    log('info', f"Person: {person_name}")
    if address:
        log('info', f"Address: {address}")
    print()

    # Step 1: Find website URL
    url = await find_website_url(firm_name, address)

    if not url:
        print()
        print("=" * 70)
        log('fail', "PIPELINE FAILED: Could not find website")
        print("=" * 70)
        return {
            "status": "failed",
            "reason": "website_not_found",
            "firm": firm_name,
            "person": person_name
        }

    print()

    # Step 2: Extract email
    result = await extract_email_from_url(url, person_name)

    print()
    print("=" * 70)

    if result and result.get('email'):
        log('ok', "PIPELINE SUCCESS")
        print("=" * 70)
        log('email', f"Email: {result['email']}")
        log('info', f"Profile: {result.get('profile_url', 'N/A')}")
        log('info', f"Confidence: {result.get('confidence', 'N/A')}")

        if result.get('is_general_contact'):
            log('warn', "Note: This is a general contact email, not personal")

        return {
            "status": "success",
            "firm": firm_name,
            "person": person_name,
            "email": result['email'],
            "profile_url": result.get('profile_url'),
            "confidence": result.get('confidence'),
            "is_general_contact": result.get('is_general_contact', False),
            "website_url": url
        }
    else:
        log('fail', "PIPELINE FAILED: Email not found")
        print("=" * 70)
        return {
            "status": "failed",
            "reason": "email_not_found",
            "firm": firm_name,
            "person": person_name,
            "website_url": url
        }

# ============== CLI INTERFACE ==============

async def main():
    """Main CLI entry point"""

    if len(sys.argv) < 3:
        print("Complete Email Extraction Pipeline")
        print("=" * 70)
        print("\nUsage:")
        print("  python complete_email_extractor.py \"Firm Name\" \"Person Name\"")
        print("  python complete_email_extractor.py \"Firm Name\" \"Address\" \"Person Name\"")
        print("\nExamples:")
        print("  python complete_email_extractor.py \"Sullivan & Cromwell\" \"Robert Giuffra\"")
        print("  python complete_email_extractor.py \"DLA Piper\" \"New York\" \"John Smith\"")
        print()
        sys.exit(1)

    # Parse arguments
    if len(sys.argv) == 3:
        firm_name = sys.argv[1]
        address = ""
        person_name = sys.argv[2]
    elif len(sys.argv) == 4:
        firm_name = sys.argv[1]
        address = sys.argv[2]
        person_name = sys.argv[3]
    else:
        print("❌ Too many arguments")
        sys.exit(1)

    # Run pipeline
    result = await complete_pipeline(firm_name, person_name, address)

    # Save result to JSON
    output_file = f"result_{firm_name.replace(' ', '_')}_{person_name.replace(' ', '_')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print()
    log('info', f"Result saved to: {output_file}")
    print()

    return result

if __name__ == "__main__":
    result = asyncio.run(main())

    # Exit with appropriate code
    sys.exit(0 if result.get('status') == 'success' else 1)
