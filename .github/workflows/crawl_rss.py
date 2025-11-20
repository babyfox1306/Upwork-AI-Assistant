#!/usr/bin/env python3
"""
Script crawl RSS Upwork và lưu vào raw_jobs.jsonl
Chạy trong GitHub Actions mỗi 15 phút

⚠️ LƯU Ý: Upwork đã ngừng hỗ trợ RSS feed từ 20/8/2024.
Cần chuyển sang dùng Upwork API. Xem UPWORK_API_SETUP.md để biết cách setup.
"""

import feedparser
import yaml
import json
import os
import re
from datetime import datetime
from urllib.parse import urlencode, quote

# Load config
with open('config/config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

rss_config = config['rss']
categories = config['categories']

# Load existing jobs để tránh duplicate
existing_job_ids = set()
raw_jobs_file = 'data/raw_jobs.jsonl'

if os.path.exists(raw_jobs_file):
    with open(raw_jobs_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    job = json.loads(line)
                    existing_job_ids.add(job.get('job_id', ''))
                except:
                    pass

# Parse job ID từ link
def extract_job_id(link):
    """Extract job ID từ Upwork link"""
    match = re.search(r'/jobs/~([a-f0-9]+)', link)
    if match:
        return match.group(1)
    return None

# Parse budget từ description
def parse_budget(description):
    """Parse budget từ job description"""
    # Tìm pattern $XXX hoặc $XXX - $YYY
    budget_match = re.search(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', description, re.IGNORECASE)
    if budget_match:
        return budget_match.group(1)
    return None

# Parse số proposals
def parse_proposals(description):
    """Parse số proposals từ description"""
    prop_match = re.search(r'(\d+)\s*(?:proposal|bid)', description, re.IGNORECASE)
    if prop_match:
        return int(prop_match.group(1))
    return None

# Parse client country
def parse_client_country(description):
    """Parse client country từ description"""
    # Thường có format "Client from [Country]"
    country_match = re.search(r'from\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', description, re.IGNORECASE)
    if country_match:
        return country_match.group(1)
    return "Unknown"

new_jobs = []

# Crawl từng category
for category in categories:
    try:
        # Build RSS URL
        params = rss_config['params'].copy()
        params['subcategory2'] = category['subcategory2']
        
        # Build query string
        query_parts = []
        for key, value in params.items():
            if value:
                query_parts.append(f"{key}={quote(str(value))}")
        
        rss_url = f"{rss_config['base_url']}?{'&'.join(query_parts)}"
        
        # Parse RSS feed
        feed = feedparser.parse(rss_url)
        
        # Debug info
        feed_status = feed.get('status', 'Unknown')
        if feed_status != 200:
            print(f"⚠ RSS feed status {feed_status} for category {category['name']}")
            if hasattr(feed, 'bozo_exception'):
                print(f"   Error: {feed.bozo_exception}")
            continue
        
        if not feed.entries:
            print(f"⚠ No entries found for category {category['name']}")
            continue
        
        print(f"✓ Found {len(feed.entries)} entries for category {category['name']}")
        
        for entry in feed.entries:
            job_id = extract_job_id(entry.link)
            
            if not job_id or job_id in existing_job_ids:
                continue
            
            # Parse job data
            description = entry.get('summary', entry.get('description', ''))
            budget = parse_budget(description)
            proposals = parse_proposals(description)
            client_country = parse_client_country(description)
            
            job_data = {
                'job_id': job_id,
                'title': entry.get('title', ''),
                'description': description,
                'link': entry.link,
                'budget': budget,
                'proposals': proposals,
                'client_country': client_country,
                'category': category['name'],
                'created_at': entry.get('published', datetime.utcnow().isoformat()),
                'crawled_at': datetime.utcnow().isoformat()
            }
            
            new_jobs.append(job_data)
            existing_job_ids.add(job_id)
            
    except Exception as e:
        print(f"❌ Error crawling category {category['name']}: {e}")
        import traceback
        traceback.print_exc()
        continue

# Append new jobs to file
if new_jobs:
    with open(raw_jobs_file, 'a', encoding='utf-8') as f:
        for job in new_jobs:
            f.write(json.dumps(job, ensure_ascii=False) + '\n')
    
    print(f"✅ Added {len(new_jobs)} new jobs")
else:
    print("ℹ️  No new jobs found")
    # Debug: Check if RSS is accessible
    test_url = rss_config['base_url']
    test_feed = feedparser.parse(test_url)
    if test_feed.get('status') == 410:
        print("=" * 60)
        print("❌ RSS FEED ĐÃ BỊ TẮT")
        print("=" * 60)
        print("Upwork đã chính thức ngừng hỗ trợ RSS feed từ 20/8/2024.")
        print("RSS endpoint trả về 410 (Gone).")
        print("")
        print("✅ GIẢI PHÁP:")
        print("   1. Request Upwork API key: https://support.upwork.com/hc/en-us/articles/17995842326931")
        print("   2. Setup OAuth 2.0 authentication")
        print("   3. Update script để dùng Upwork API thay vì RSS")
        print("   4. Xem chi tiết trong file: UPWORK_API_SETUP.md")
        print("")
        print("💡 TẠM THỜI:")
        print("   - Có thể tạo sample data để test hệ thống")
        print("   - Hoặc dùng service UpNotify: https://upnotify.me/")
        print("=" * 60)

