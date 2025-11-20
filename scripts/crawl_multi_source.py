#!/usr/bin/env python3
"""
Script crawl jobs từ nhiều nguồn uy tín (không chỉ Upwork)
Hỗ trợ RSS feeds, APIs, và có thể mở rộng cho web scraping
"""

import feedparser
import yaml
import json
import os
import re
import requests
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode, quote

# Load config
config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

sources = config.get('sources', {})
keywords = config.get('search_keywords', [])

# Load existing jobs
existing_job_ids = set()
raw_jobs_file = Path(__file__).parent.parent / 'data' / 'raw_jobs.jsonl'

if raw_jobs_file.exists():
    with open(raw_jobs_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    job = json.loads(line)
                    existing_job_ids.add(job.get('job_id', ''))
                except:
                    pass

def generate_job_id(title, link, source):
    """Generate unique job ID từ title, link và source"""
    import hashlib
    combined = f"{source}_{title}_{link}"
    return hashlib.md5(combined.encode()).hexdigest()[:12]

def parse_budget(text):
    """Parse budget từ text"""
    # Tìm $XXX hoặc $XXX - $YYY
    budget_match = re.search(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
    if budget_match:
        return budget_match.group(1)
    return None

def parse_proposals(text):
    """Parse số proposals/bids từ text"""
    prop_match = re.search(r'(\d+)\s*(?:proposal|bid|applicant)', text, re.IGNORECASE)
    if prop_match:
        return int(prop_match.group(1))
    return None

def normalize_job(entry, source_name, source_type):
    """Normalize job data từ các nguồn khác nhau về cùng format"""
    title = entry.get('title', '')
    link = entry.get('link', entry.get('url', ''))
    description = entry.get('summary', entry.get('description', entry.get('content', '')))
    
    job_id = generate_job_id(title, link, source_name)
    
    if job_id in existing_job_ids:
        return None
    
    # Parse metadata
    budget = parse_budget(description or title)
    proposals = parse_proposals(description or title)
    
    # Extract location/client country
    location = entry.get('location', entry.get('where', ''))
    if not location:
        location_match = re.search(r'(?:from|in|location)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 
                                  description or '', re.IGNORECASE)
        if location_match:
            location = location_match.group(1)
    
    # Determine category từ keywords
    category = "General"
    description_lower = (description or '').lower()
    for keyword in keywords:
        if keyword.lower() in description_lower or keyword.lower() in title.lower():
            category = keyword
            break
    
    job_data = {
        'job_id': job_id,
        'title': title,
        'description': description or '',
        'link': link,
        'budget': budget,
        'proposals': proposals,
        'client_country': location or 'Unknown',
        'category': category,
        'source': source_name,
        'source_type': source_type,
        'created_at': entry.get('published', entry.get('created_at', datetime.utcnow().isoformat())),
        'crawled_at': datetime.utcnow().isoformat()
    }
    
    return job_data

def crawl_rss_feed(feed_config):
    """Crawl từ RSS feed"""
    if not feed_config.get('enabled', False):
        return []
    
    url = feed_config['url']
    name = feed_config['name']
    
    try:
        feed = feedparser.parse(url)
        
        if feed.get('status') != 200:
            print(f"⚠ RSS feed {name} status {feed.get('status')}")
            return []
        
        if not feed.entries:
            print(f"⚠ No entries in {name}")
            return []
        
        print(f"✓ Found {len(feed.entries)} entries from {name}")
        
        jobs = []
        for entry in feed.entries:
            job = normalize_job(entry, name, 'rss')
            if job:
                jobs.append(job)
                existing_job_ids.add(job['job_id'])
        
        return jobs
    
    except Exception as e:
        print(f"❌ Error crawling {name}: {e}")
        return []

def crawl_api_source(api_config):
    """Crawl từ API"""
    if not api_config.get('enabled', False):
        return []
    
    url = api_config['url']
    name = api_config['name']
    params = api_config.get('params', {})
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not isinstance(data, list):
            data = [data]
        
        print(f"✓ Found {len(data)} entries from {name}")
        
        jobs = []
        for item in data:
            # Convert API response to entry format
            entry = {
                'title': item.get('title', item.get('name', '')),
                'link': item.get('url', item.get('link', '')),
                'description': item.get('description', item.get('summary', '')),
                'location': item.get('location', ''),
                'published': item.get('created_at', item.get('date', ''))
            }
            
            job = normalize_job(entry, name, 'api')
            if job:
                jobs.append(job)
                existing_job_ids.add(job['job_id'])
        
        return jobs
    
    except Exception as e:
        print(f"❌ Error crawling {name}: {e}")
        return []

def main():
    """Main crawl function"""
    print("=" * 60)
    print("🔄 Bắt đầu crawl jobs từ nhiều nguồn uy tín...")
    print("=" * 60)
    
    all_jobs = []
    
    # Crawl RSS feeds
    rss_feeds = sources.get('rss_feeds', [])
    for feed_config in rss_feeds:
        jobs = crawl_rss_feed(feed_config)
        all_jobs.extend(jobs)
    
    # Crawl API sources
    api_sources = sources.get('api_sources', [])
    for api_config in api_sources:
        jobs = crawl_api_source(api_config)
        all_jobs.extend(jobs)
    
    # Save jobs
    if all_jobs:
        with open(raw_jobs_file, 'a', encoding='utf-8') as f:
            for job in all_jobs:
                f.write(json.dumps(job, ensure_ascii=False) + '\n')
        
        print(f"\n✅ Đã thêm {len(all_jobs)} jobs mới từ {len(set(j['source'] for j in all_jobs))} nguồn")
    else:
        print("\nℹ️  Không tìm thấy jobs mới")
    
    print("=" * 60)

if __name__ == '__main__':
    main()

