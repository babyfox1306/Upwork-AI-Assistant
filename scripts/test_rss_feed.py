#!/usr/bin/env python3
"""
Script test RSS feeds - Kiểm tra feeds trước khi thêm vào config
Usage:
    python scripts/test_rss_feed.py <url>
    python scripts/test_rss_feed.py --file test_feeds.yaml
"""

import sys
import yaml
import feedparser
import requests
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import setup_logger

logger = setup_logger('test_rss_feed')

def test_single_feed(url, name="Test Feed", timeout=10):
    """
    Test một RSS feed
    
    Returns:
        dict với keys: success, status, entries_count, error, sample_entries
    """
    result = {
        'url': url,
        'name': name,
        'success': False,
        'status': None,
        'entries_count': 0,
        'error': None,
        'sample_entries': [],
        'response_time': None,
        'feed_type': None
    }
    
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    try:
        # Test với requests trước để check status
        start_time = time.time()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            response_time = time.time() - start_time
            result['response_time'] = round(response_time, 2)
            result['status'] = response.status_code
            
            if response.status_code != 200:
                result['error'] = f"HTTP {response.status_code}"
                print(f"[FAIL] HTTP Status: {response.status_code}")
                return result
        except requests.Timeout:
            result['error'] = f"Timeout after {timeout}s"
            print(f"[FAIL] Timeout after {timeout}s")
            return result
        except requests.RequestException as e:
            result['error'] = f"Request error: {str(e)[:50]}"
            print(f"[FAIL] Request error: {e}")
            return result
        
        # Parse RSS feed
        feed = feedparser.parse(url)
        
        # Check feed status
        feed_status = feed.get('status', 200)
        if feed_status not in [200, 301, 302]:
            result['error'] = f"Feed status: {feed_status}"
            print(f"[FAIL] Feed status: {feed_status}")
            return result
        
        # Check parsing errors
        if hasattr(feed, 'bozo') and feed.bozo:
            if hasattr(feed, 'bozo_exception'):
                result['error'] = f"Parse error: {str(feed.bozo_exception)[:100]}"
                print(f"[FAIL] Parse error: {feed.bozo_exception}")
            else:
                result['error'] = "Parse error (unknown)"
                print(f"[FAIL] Parse error (unknown)")
            return result
        
        # Check entries
        entries = feed.entries
        result['entries_count'] = len(entries)
        
        if len(entries) == 0:
            result['error'] = "No entries found"
            print(f"[WARN] No entries found")
            return result
        
        # Get feed info
        feed_title = feed.feed.get('title', 'Unknown')
        feed_link = feed.feed.get('link', '')
        result['feed_type'] = feed.feed.get('version', 'Unknown')
        
        # Sample entries
        sample_count = min(3, len(entries))
        for i, entry in enumerate(entries[:sample_count]):
            sample = {
                'title': entry.get('title', 'No title')[:80],
                'link': entry.get('link', ''),
                'published': entry.get('published', entry.get('updated', 'Unknown'))
            }
            result['sample_entries'].append(sample)
        
        # Success!
        result['success'] = True
        result['feed_title'] = feed_title
        result['feed_link'] = feed_link
        
        print(f"[OK] SUCCESS!")
        print(f"   Status: {feed_status}")
        print(f"   Response time: {response_time:.2f}s")
        print(f"   Feed type: {result['feed_type']}")
        print(f"   Feed title: {feed_title}")
        print(f"   Entries found: {len(entries)}")
        print(f"\n   Sample entries:")
        for i, entry in enumerate(result['sample_entries'], 1):
            print(f"   {i}. {entry['title']}")
            print(f"      Link: {entry['link'][:60]}...")
            print(f"      Published: {entry['published']}")
        
        return result
        
    except Exception as e:
        result['error'] = f"Unexpected error: {str(e)[:100]}"
        logger.error(f"Error testing feed {url}: {e}", exc_info=True)
        print(f"[FAIL] Unexpected error: {e}")
        return result

def test_from_file(file_path):
    """Test nhiều feeds từ file YAML"""
    with open(file_path, 'r', encoding='utf-8') as f:
        feeds = yaml.safe_load(f)
    
    results = []
    for feed in feeds.get('feeds', []):
        result = test_single_feed(
            url=feed['url'],
            name=feed.get('name', 'Unnamed'),
            timeout=feed.get('timeout', 10)
        )
        results.append(result)
        time.sleep(1)  # Rate limiting
    
    return results

def generate_config_entry(result):
    """Generate config YAML entry từ test result"""
    if not result['success']:
        return None
    
    entry = {
        'name': result['name'],
        'url': result['url'],
        'enabled': True,
        'category': 'jobs'  # Default, có thể chỉnh sau
    }
    
    return entry

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Test RSS feeds trước khi thêm vào config')
    parser.add_argument('url', nargs='?', help='RSS feed URL để test')
    parser.add_argument('--name', default='Test Feed', help='Tên feed (optional)')
    parser.add_argument('--file', help='File YAML chứa danh sách feeds để test')
    parser.add_argument('--timeout', type=int, default=10, help='Timeout (seconds)')
    parser.add_argument('--export', action='store_true', help='Export feeds OK ra config format')
    
    args = parser.parse_args()
    
    if args.file:
        # Test từ file
        print(f"Testing feeds from: {args.file}")
        results = test_from_file(args.file)
        
        # Summary
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        success_count = sum(1 for r in results if r['success'])
        total_count = len(results)
        
        print(f"Total: {total_count}")
        print(f"Success: {success_count}")
        print(f"Failed: {total_count - success_count}")
        
        # Export nếu cần
        if args.export:
            successful_feeds = [r for r in results if r['success']]
            if successful_feeds:
                print(f"\n{'='*60}")
                print("CONFIG ENTRIES (copy vào config.yaml):")
                print(f"{'='*60}")
                for result in successful_feeds:
                    entry = generate_config_entry(result)
                    if entry:
                        print(f"\n  - name: \"{entry['name']}\"")
                        print(f"    url: \"{entry['url']}\"")
                        print(f"    enabled: true")
                        print(f"    category: \"{entry['category']}\"")
        
    elif args.url:
        # Test single feed
        result = test_single_feed(args.url, args.name, args.timeout)
        
        if result['success']:
            print(f"\n{'='*60}")
            print("[OK] FEED IS READY TO ADD TO CONFIG")
            print(f"{'='*60}")
            print("\nConfig entry:")
            entry = generate_config_entry(result)
            if entry:
                print(f"  - name: \"{entry['name']}\"")
                print(f"    url: \"{entry['url']}\"")
                print(f"    enabled: true")
                print(f"    category: \"{entry['category']}\"")
        else:
            print(f"\n{'='*60}")
            print("[FAIL] FEED FAILED - DO NOT ADD TO CONFIG")
            print(f"{'='*60}")
            print(f"Error: {result['error']}")
            return 1
    else:
        parser.print_help()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

