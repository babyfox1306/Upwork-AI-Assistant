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
import sys

# Add parent directory to path for utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import setup_logger
from utils.validation import validate_job, sanitize_job

# Setup logger
logger = setup_logger('crawl_multi_source')

# Load config
config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

sources = config.get('sources', {})
keywords = config.get('search_keywords', [])
crawl_config = config.get('crawl', {})
timeout_per_source = crawl_config.get('timeout_per_source', 5)
max_workers = crawl_config.get('max_workers', 8)

# Load existing jobs
existing_job_ids = set()
raw_jobs_file = Path(__file__).parent.parent / 'data' / 'raw_jobs.jsonl'

if raw_jobs_file.exists():
    with open(raw_jobs_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if line.strip():
                try:
                    job = json.loads(line)
                    job_id = job.get('job_id', '')
                    if job_id:
                        existing_job_ids.add(job_id)
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON at line {line_num} in raw_jobs.jsonl: {e}")
                except Exception as e:
                    logger.error(f"Error loading existing job at line {line_num}: {e}")

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
    
    # Sanitize and validate
    job_data = sanitize_job(job_data)
    is_valid, errors = validate_job(job_data)
    
    if not is_valid:
        logger.warning(f"Invalid job data from {source_name}: {', '.join(errors)}")
        return None
    
    return job_data

def crawl_rss_feed(feed_config):
    """Crawl từ RSS feed, return (jobs, error_msg)"""
    if not feed_config.get('enabled', False):
        return ([], None)
    
    url = feed_config['url']
    name = feed_config['name']
    
    try:
        # Add User-Agent để tránh bị block
        import urllib.request
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        feed = feedparser.parse(url)
        
        status = feed.get('status', 200)
        error_msg = None
        
        if status not in [200, 301, 302]:  # Allow redirects
            error_msg = f"HTTP {status}"
            logger.warning(f"RSS feed {name} returned status {status}")
            return ([], error_msg)
        
        # Check bozo (parsing errors)
        if hasattr(feed, 'bozo') and feed.bozo:
            if hasattr(feed, 'bozo_exception'):
                error_msg = f"Parse error: {str(feed.bozo_exception)[:40]}"
                logger.warning(f"RSS feed {name} parse error: {feed.bozo_exception}")
            else:
                error_msg = "Parse error"
                logger.warning(f"RSS feed {name} parse error (unknown)")
            return ([], error_msg)
        
        if not feed.entries:
            logger.debug(f"RSS feed {name} has no entries")
            return ([], None)
        
        jobs = []
        for entry in feed.entries:
            try:
                job = normalize_job(entry, name, 'rss')
                if job:
                    jobs.append(job)
                    existing_job_ids.add(job['job_id'])
            except Exception as e:
                logger.error(f"Error normalizing job from {name}: {e}")
                continue
        
        logger.info(f"RSS feed {name}: found {len(jobs)} new jobs")
        return (jobs, None)
    
    except Exception as e:
        error_msg = str(e)[:50]
        logger.error(f"Error crawling RSS feed {name}: {e}", exc_info=True)
        return ([], error_msg)

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
            try:
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
            except Exception as e:
                logger.error(f"Error processing API item from {name}: {e}")
                continue
        
        logger.info(f"API source {name}: found {len(jobs)} new jobs")
        return jobs
    
    except requests.RequestException as e:
        logger.error(f"API request error for {name}: {e}")
        raise Exception(f"{name}: {str(e)[:50]}")
    except Exception as e:
        logger.error(f"Error crawling API source {name}: {e}", exc_info=True)
        raise Exception(f"{name}: {str(e)[:50]}")

def main():
    """Main crawl function với parallel processing"""
    print("=" * 60)
    print("🔄 Bắt đầu crawl jobs từ nhiều nguồn uy tín...")
    print("=" * 60)
    
    all_jobs = []
    
    # Crawl job boards RSS
    job_boards = sources.get('job_boards', [])
    enabled_job_boards = [f for f in job_boards if f.get('enabled', False)]
    print(f"\n📡 Crawling {len(enabled_job_boards)} job board feeds (parallel, timeout {timeout_per_source}s each)...")
    
    def crawl_with_timeout(feed_config, index, total):
        """Crawl với timeout"""
        try:
            jobs, error_msg = crawl_rss_feed(feed_config)
            return (index, feed_config['name'], jobs, error_msg)
        except Exception as e:
            return (index, feed_config['name'], [], str(e)[:50])
    
    # Chạy song song
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(crawl_with_timeout, feed, i+1, len(enabled_job_boards)): feed 
            for i, feed in enumerate(enabled_job_boards)
        }
        
        results = []
        try:
            # Tăng overall timeout để đủ cho tất cả feeds
            overall_timeout = (timeout_per_source * len(enabled_job_boards) // max_workers) + (timeout_per_source * 2)
            for future in as_completed(futures, timeout=overall_timeout):
                try:
                    result = future.result(timeout=timeout_per_source)
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
        
        # Sort theo index và print (loại bỏ duplicate)
        results_dict = {}
        for result in results:
            index, name, jobs, error = result
            # Chỉ giữ kết quả đầu tiên nếu có duplicate
            if index not in results_dict:
                results_dict[index] = result
        
        # Sort và print
        sorted_results = sorted(results_dict.values(), key=lambda x: x[0])
        for index, name, jobs, error in sorted_results:
            if error:
                print(f"[{index}/{len(enabled_job_boards)}] {name}... ✗ {error}")
            else:
                all_jobs.extend(jobs)
                print(f"[{index}/{len(enabled_job_boards)}] {name}... ✓ {len(jobs)} jobs")
    
    # Crawl tech blogs (trends) - chỉ lưu metadata, không phải jobs
    # Skip trong GitHub Actions để tiết kiệm thời gian
    skip_tech_blogs = crawl_config.get('skip_tech_blogs_in_ci', False)
    is_ci = os.getenv('CI', 'false').lower() == 'true' or os.getenv('GITHUB_ACTIONS', 'false').lower() == 'true'
    
    tech_blogs = sources.get('tech_blogs', [])
    enabled_blogs = [f for f in tech_blogs if f.get('enabled', False)]
    
    if skip_tech_blogs and is_ci:
        print(f"\n⏭️  Skipping {len(enabled_blogs)} tech blog feeds (CI mode - chỉ crawl job boards)")
    elif enabled_blogs:
        print(f"\n📚 Crawling {len(enabled_blogs)} tech blog feeds (trends)...")
        feeds_dir = Path(__file__).parent.parent / 'data' / 'feeds'
        feeds_dir.mkdir(parents=True, exist_ok=True)
        
        for i, blog in enumerate(enabled_blogs, 1):
            print(f"[{i}/{len(enabled_blogs)}] {blog['name']}...", end=' ', flush=True)
            try:
                feed = feedparser.parse(blog['url'])
                if feed.entries:
                    # Lưu trends vào file riêng
                    trends_file = feeds_dir / f"trends_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
                    with open(trends_file, 'a', encoding='utf-8') as f:
                        for entry in feed.entries[:5]:  # Lấy 5 bài mới nhất
                            trend_data = {
                                'title': entry.get('title', ''),
                                'link': entry.get('link', ''),
                                'summary': entry.get('summary', '')[:500],
                                'source': blog['name'],
                                'published': entry.get('published', ''),
                                'crawled_at': datetime.utcnow().isoformat()
                            }
                            f.write(json.dumps(trend_data, ensure_ascii=False) + '\n')
                    print(f"✓ {len(feed.entries)} articles")
                else:
                    print("✓ 0 articles")
            except Exception as e:
                print(f"✗ {str(e)[:50]}")
    
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
    
    # TODO: HackerNews "Who is Hiring" parser (cần BeautifulSoup)
    # Có thể implement sau nếu cần
    
    # Save jobs
    print(f"\n💾 Đang lưu {len(all_jobs)} jobs...")
    logger.info(f"Saving {len(all_jobs)} new jobs to {raw_jobs_file}")
    
    if all_jobs:
        saved_count = 0
        skipped_count = 0
        
        with open(raw_jobs_file, 'a', encoding='utf-8') as f:
            for job in all_jobs:
                try:
                    # Final validation before saving
                    is_valid, errors = validate_job(job)
                    if not is_valid:
                        logger.warning(f"Skipping invalid job {job.get('job_id', 'unknown')}: {', '.join(errors)}")
                        skipped_count += 1
                        continue
                    
                    f.write(json.dumps(job, ensure_ascii=False) + '\n')
                    saved_count += 1
                except Exception as e:
                    logger.error(f"Error saving job {job.get('job_id', 'unknown')}: {e}")
                    skipped_count += 1
                    continue
        
        sources_count = len(set(j['source'] for j in all_jobs))
        print(f"\n✅ Đã thêm {saved_count} jobs mới từ {sources_count} nguồn")
        if skipped_count > 0:
            print(f"⚠️  Đã bỏ qua {skipped_count} jobs không hợp lệ")
            logger.warning(f"Skipped {skipped_count} invalid jobs")
        logger.info(f"Successfully saved {saved_count} jobs from {sources_count} sources")
    else:
        print("\nℹ️  Không tìm thấy jobs mới")
        logger.info("No new jobs found")
    
    print("=" * 60)

if __name__ == '__main__':
    main()

