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
from concurrent.futures import ThreadPoolExecutor, as_completed
import signal

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
        # Add User-Agent để tránh bị block
        import urllib.request
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        feed = feedparser.parse(url)
        
        status = feed.get('status', 200)
        if status not in [200, 301, 302]:  # Allow redirects
            print(f"⚠ RSS feed {name} status {status}")
            if hasattr(feed, 'bozo_exception'):
                print(f"   Error: {feed.bozo_exception}")
            return []
        
        if not feed.entries:
            return []
        
        # Return count, don't print here (will print in main)
        
        jobs = []
        for entry in feed.entries:
            job = normalize_job(entry, name, 'rss')
            if job:
                jobs.append(job)
                existing_job_ids.add(job['job_id'])
        
        return jobs
    
    except Exception as e:
        raise Exception(f"{name}: {str(e)[:50]}")

def crawl_api_source(api_config):
    """Crawl từ API"""
    if not api_config.get('enabled', False):
        return []
    
    url = api_config['url']
    name = api_config['name']
    params = api_config.get('params', {})
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if not isinstance(data, list):
            data = [data]
        
        # Filter out invalid entries
        valid_data = [item for item in data if item and isinstance(item, dict)]
        
        # Return count, don't print here (will print in main)
        
        jobs = []
        for item in valid_data:
            # RemoteOK API format
            if 'slug' in item or 'id' in item:
                entry = {
                    'title': item.get('position', item.get('title', item.get('name', ''))),
                    'link': item.get('url', item.get('apply_url', f"https://remoteok.io/remote-jobs/{item.get('id', '')}")),
                    'description': item.get('description', item.get('summary', '')),
                    'location': item.get('location', item.get('location_name', 'Remote')),
                    'published': item.get('epoch', item.get('created_at', item.get('date', '')))
                }
            else:
                # Generic API format
                entry = {
                    'title': item.get('title', item.get('name', '')),
                    'link': item.get('url', item.get('link', item.get('apply_url', ''))),
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
        raise Exception(f"{name}: {str(e)[:50]}")

def main():
    """Main crawl function với parallel processing"""
    print("=" * 60)
    print("🔄 Bắt đầu crawl jobs từ nhiều nguồn uy tín...")
    print("=" * 60)
    
    all_jobs = []
    
    # Crawl RSS feeds - chạy song song với timeout
    rss_feeds = sources.get('rss_feeds', [])
    enabled_feeds = [f for f in rss_feeds if f.get('enabled', False)]
    print(f"\n📡 Crawling {len(enabled_feeds)} RSS feeds (parallel, timeout 5s each)...")
    
    def crawl_with_timeout(feed_config, index, total):
        """Crawl với timeout"""
        try:
            jobs = crawl_rss_feed(feed_config)
            return (index, feed_config['name'], jobs, None)
        except Exception as e:
            return (index, feed_config['name'], [], str(e))
    
    # Chạy song song tối đa 5 threads
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(crawl_with_timeout, feed, i+1, len(enabled_feeds)): feed 
            for i, feed in enumerate(enabled_feeds)
        }
        
        results = []
        try:
            for future in as_completed(futures, timeout=30):  # Tổng timeout 30s
                try:
                    result = future.result(timeout=5)
                    results.append(result)
                except Exception as e:
                    feed_name = futures[future]['name']
                    results.append((0, feed_name, [], f"Timeout: {str(e)[:30]}"))
        except Exception as e:
            # Nếu timeout toàn bộ, lấy kết quả đã có
            print(f"⚠ Overall timeout, using partial results: {str(e)[:50]}")
            for future in futures:
                if future.done():
                    try:
                        results.append(future.result())
                    except:
                        pass
        
        # Sort theo index và print
        results.sort(key=lambda x: x[0])
        for index, name, jobs, error in results:
            if error:
                print(f"[{index}/{len(enabled_feeds)}] {name}... ✗ {error}")
            else:
                all_jobs.extend(jobs)
                print(f"[{index}/{len(enabled_feeds)}] {name}... ✓ {len(jobs)} jobs")
    
    # Crawl API sources
    api_sources = sources.get('api_sources', [])
    enabled_apis = [a for a in api_sources if a.get('enabled', False)]
    if enabled_apis:
        print(f"\n🔌 Crawling {len(enabled_apis)} API sources...")
        for i, api_config in enumerate(enabled_apis, 1):
            print(f"[{i}/{len(enabled_apis)}] {api_config['name']}...", end=' ', flush=True)
            try:
                jobs = crawl_api_source(api_config)
                all_jobs.extend(jobs)
                print(f"✓ {len(jobs)} jobs")
            except Exception as e:
                print(f"✗ {str(e)[:50]}")
    
    # Save jobs
    print(f"\n💾 Đang lưu {len(all_jobs)} jobs...")
    if all_jobs:
        with open(raw_jobs_file, 'a', encoding='utf-8') as f:
            for job in all_jobs:
                f.write(json.dumps(job, ensure_ascii=False) + '\n')
        
        sources_count = len(set(j['source'] for j in all_jobs))
        print(f"\n✅ Đã thêm {len(all_jobs)} jobs mới từ {sources_count} nguồn")
    else:
        print("\nℹ️  Không tìm thấy jobs mới")
    
    print("=" * 60)

if __name__ == '__main__':
    main()

