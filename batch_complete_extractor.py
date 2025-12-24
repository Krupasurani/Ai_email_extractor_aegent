#!/usr/bin/env python3
"""
Batch Complete Email Extractor
===============================
Process multiple firms/people from a CSV file.

Input CSV format:
    firm_name,address,person_name
    Sullivan & Cromwell,New York,Robert Giuffra
    DLA Piper,Chicago,John Smith
    Skadden,Boston,Jane Doe

Usage:
    python batch_complete_extractor.py input.csv
"""

import os
import sys
import csv
import asyncio
import json
from datetime import datetime
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

from complete_email_extractor import complete_pipeline

# ============== CONFIG ==============

OUTPUT_CSV = "batch_complete_results.csv"
OUTPUT_JSON = "batch_complete_results.json"
MAX_WORKERS = 2  # Number of parallel extractions
TIMEOUT = 180  # seconds per extraction

CSV_HEADERS = [
    "timestamp", "firm_name", "address", "person_name",
    "status", "email", "profile_url", "website_url",
    "confidence", "is_general_contact", "runtime_sec", "error"
]

# ============== FUNCTIONS ==============

def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def run_extraction(firm_name: str, person_name: str, address: str = "") -> Dict:
    """Run one complete extraction"""
    import time
    start = time.time()

    result = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "firm_name": firm_name.strip(),
        "address": address.strip(),
        "person_name": person_name.strip(),
        "status": "failed",
        "email": "",
        "profile_url": "",
        "website_url": "",
        "confidence": "",
        "is_general_contact": False,
        "runtime_sec": 0,
        "error": ""
    }

    try:
        # Run async pipeline
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        pipeline_result = loop.run_until_complete(
            complete_pipeline(firm_name, person_name, address)
        )
        loop.close()

        # Map pipeline result to CSV result
        result["status"] = pipeline_result.get("status", "failed")
        result["email"] = pipeline_result.get("email", "")
        result["profile_url"] = pipeline_result.get("profile_url", "")
        result["website_url"] = pipeline_result.get("website_url", "")
        result["confidence"] = pipeline_result.get("confidence", "")
        result["is_general_contact"] = pipeline_result.get("is_general_contact", False)
        result["error"] = pipeline_result.get("reason", "")

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)[:100]
        log(f"❌ Error: {firm_name} / {person_name} - {str(e)[:50]}")

    result["runtime_sec"] = round(time.time() - start, 2)
    return result

def load_input_csv(file_path: str) -> List[Dict]:
    """Load input CSV file"""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    rows = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        # Support both formats:
        # 1. firm_name,address,person_name
        # 2. firm_name,person_name (no address)

        for row in reader:
            # Clean field names
            row = {k.strip(): v.strip() for k, v in row.items()}

            firm = row.get('firm_name') or row.get('firm') or row.get('company') or ""
            person = row.get('person_name') or row.get('person') or row.get('name') or ""
            address = row.get('address') or row.get('location') or row.get('city') or ""

            if not firm or not person:
                log(f"⚠️ Skipping invalid row: {row}")
                continue

            rows.append({
                "firm_name": firm,
                "person_name": person,
                "address": address
            })

    return rows

def save_results(results: List[Dict]):
    """Save results to CSV and JSON"""

    # Save CSV
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(results)

    log(f"📁 CSV saved to: {OUTPUT_CSV}")

    # Save JSON
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    log(f"📁 JSON saved to: {OUTPUT_JSON}")

def print_summary(results: List[Dict]):
    """Print summary statistics"""
    total = len(results)
    success = sum(1 for r in results if r['status'] == 'success')
    failed = sum(1 for r in results if r['status'] == 'failed')
    errors = sum(1 for r in results if r['status'] == 'error')

    print()
    print("=" * 70)
    print("📊 BATCH PROCESSING SUMMARY")
    print("=" * 70)
    print(f"Total Cases:     {total}")
    print(f"✅ Success:      {success} ({success/total*100:.1f}%)")
    print(f"❌ Failed:       {failed} ({failed/total*100:.1f}%)")
    print(f"⚠️ Errors:       {errors} ({errors/total*100:.1f}%)")
    print("=" * 70)

    if success > 0:
        print("\n✅ Successfully extracted emails:")
        for r in results:
            if r['status'] == 'success':
                contact_note = " [General Contact]" if r['is_general_contact'] else ""
                print(f"   • {r['person_name']} @ {r['firm_name']}: {r['email']}{contact_note}")

# ============== MAIN ==============

def main():
    if len(sys.argv) < 2:
        print("Batch Complete Email Extractor")
        print("=" * 70)
        print("\nUsage:")
        print("  python batch_complete_extractor.py input.csv")
        print("\nInput CSV format:")
        print("  firm_name,address,person_name")
        print("  Sullivan & Cromwell,New York,Robert Giuffra")
        print("  DLA Piper,Chicago,John Smith")
        print("\nOr without address:")
        print("  firm_name,person_name")
        print("  Sullivan & Cromwell,Robert Giuffra")
        print()
        sys.exit(1)

    input_file = sys.argv[1]

    # Load input
    rows = load_input_csv(input_file)
    log(f"📋 Loaded {len(rows)} cases from {input_file}")
    print()

    # Process with thread pool
    results = []
    print("=" * 70)
    log("🚀 Starting batch processing...")
    print("=" * 70)
    print()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(
                run_extraction,
                row['firm_name'],
                row['person_name'],
                row['address']
            ): row for row in rows
        }

        for i, future in enumerate(as_completed(futures), start=1):
            row = futures[future]
            res = future.result()
            results.append(res)

            status_icon = "✅" if res['status'] == 'success' else "❌"
            email_info = res['email'] or "None"

            log(f"[{i}/{len(rows)}] {status_icon} {res['person_name']} @ {res['firm_name']} → {res['status']} ({email_info})")

    # Save results
    print()
    save_results(results)

    # Print summary
    print_summary(results)

    print()

if __name__ == "__main__":
    main()
