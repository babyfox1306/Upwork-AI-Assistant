#!/usr/bin/env python3
"""
Script tích hợp: Phân tích jobs mới và generate summary
Chạy local sau khi pull data từ GitHub
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai.analyser import analyse_job
from ai.summarizer import generate_daily_summary, generate_weekly_summary
import json

def main():
    """Analyze new jobs and generate summaries"""
    print("=" * 60)
    print("🤖 AI Analysis & Summary")
    print("=" * 60)
    
    # Load new jobs
    jobs_file = Path(__file__).parent.parent / 'data' / 'raw_jobs.jsonl'
    if not jobs_file.exists():
        print("❌ Không tìm thấy data/raw_jobs.jsonl")
        return
    
    # Load jobs từ 24h gần đây
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(hours=24)
    new_jobs = []
    
    with open(jobs_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    job = json.loads(line)
                    crawled_at = job.get('crawled_at', '')
                    if crawled_at:
                        try:
                            job_date = datetime.fromisoformat(crawled_at.replace('Z', '+00:00'))
                            if job_date >= cutoff:
                                new_jobs.append(job)
                        except:
                            pass
                except:
                    pass
    
    print(f"\n📊 Tìm thấy {len(new_jobs)} jobs mới trong 24h")
    
    if not new_jobs:
        print("ℹ️  Không có job mới để phân tích")
    else:
        # Analyze top 10 jobs (để không tốn thời gian)
        print(f"\n🔍 Phân tích top 10 jobs...")
        analyzed = []
        for i, job in enumerate(new_jobs[:10], 1):
            print(f"[{i}/10] Analyzing: {job.get('title', 'N/A')[:50]}...", end=' ', flush=True)
            try:
                analysis = analyse_job(job)
                analyzed.append({
                    'job': job,
                    'analysis': analysis
                })
                print("✓")
            except Exception as e:
                print(f"✗ Error: {str(e)[:30]}")
        
        # Save analyses
        if analyzed:
            analyses_dir = Path(__file__).parent.parent / 'data' / 'analyses'
            analyses_dir.mkdir(parents=True, exist_ok=True)
            
            analyses_file = analyses_dir / f"analyses_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
            with open(analyses_file, 'w', encoding='utf-8') as f:
                for item in analyzed:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
            
            print(f"\n✅ Đã lưu {len(analyzed)} analyses vào {analyses_file.name}")
    
    # Generate daily summary
    print(f"\n📝 Generating daily summary...")
    try:
        daily_summary = generate_daily_summary()
        print(f"✅ Daily summary: {daily_summary.get('total_jobs', 0)} jobs")
        print(f"   Top keywords: {', '.join([k['keyword'] for k in daily_summary.get('top_keywords', [])[:5]])}")
    except Exception as e:
        print(f"✗ Error generating daily summary: {str(e)[:50]}")
    
    # Generate weekly summary (chỉ chạy vào Chủ nhật)
    from datetime import datetime
    if datetime.utcnow().weekday() == 6:  # Sunday
        print(f"\n📊 Generating weekly summary...")
        try:
            weekly_summary = generate_weekly_summary()
            print(f"✅ Weekly summary: {weekly_summary.get('total_jobs', 0)} jobs")
        except Exception as e:
            print(f"✗ Error generating weekly summary: {str(e)[:50]}")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    main()

