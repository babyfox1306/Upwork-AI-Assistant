#!/usr/bin/env python3
"""
Script crawl RSS Upwork và lưu vào raw_jobs.jsonl
Chạy trong GitHub Actions mỗi 15 phút
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
        print(f"Error crawling category {category['name']}: {e}")
        continue

# Append new jobs to file
if new_jobs:
    with open(raw_jobs_file, 'a', encoding='utf-8') as f:
        for job in new_jobs:
            f.write(json.dumps(job, ensure_ascii=False) + '\n')
    
    print(f"Added {len(new_jobs)} new jobs")
else:
    print("No new jobs found")

