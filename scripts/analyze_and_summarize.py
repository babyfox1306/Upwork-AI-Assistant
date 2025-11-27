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
from utils.logger import setup_logger
import json

# Setup logger
logger = setup_logger('analyze_and_summarize')

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
        # Skip AI analysis nếu không có jobs mới
        analyzed = []
    elif len(new_jobs) > 50:
        # Nếu quá nhiều jobs mới, chỉ phân tích top 3 để tiết kiệm thời gian
        print(f"\n⚠️  Quá nhiều jobs mới ({len(new_jobs)}), chỉ phân tích top 3...")
        analyzed = []
        for i, job in enumerate(new_jobs[:3], 1):
            print(f"[{i}/3] Analyzing: {job.get('title', 'N/A')[:50]}...", end=' ', flush=True)
            try:
                from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
                
                def run_analysis():
                    return analyse_job(job)
                
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(run_analysis)
                    try:
                        analysis = future.result(timeout=60)
                        analyzed.append({
                            'job': job,
                            'analysis': analysis
                        })
                        print("[OK]")
                    except FutureTimeoutError:
                        print("[TIMEOUT]")
                        logger.warning(f"AI analysis timeout for job {job.get('job_id', 'unknown')}")
            except Exception as e:
                print(f"[FAIL] Error: {str(e)[:30]}")
                logger.error(f"Error analyzing job {job.get('job_id', 'unknown')}: {e}")
    else:
        # Analyze top 5 jobs (giảm từ 10 xuống 5 để nhanh hơn)
        print(f"\n🔍 Phân tích top 5 jobs...")
        analyzed = []
        for i, job in enumerate(new_jobs[:5], 1):
            print(f"[{i}/5] Analyzing: {job.get('title', 'N/A')[:50]}...", end=' ', flush=True)
            try:
                # Thêm timeout cho AI analysis (60 giây mỗi job) - dùng threading cho cross-platform
                from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
                import threading
                
                def run_analysis():
                    return analyse_job(job)
                
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(run_analysis)
                    try:
                        analysis = future.result(timeout=60)  # 60 seconds timeout
                        analyzed.append({
                            'job': job,
                            'analysis': analysis
                        })
                        print("[OK]")
                    except FutureTimeoutError:
                        print("[TIMEOUT]")
                        logger.warning(f"AI analysis timeout for job {job.get('job_id', 'unknown')} after 60s")
                        future.cancel()
            except Exception as e:
                print(f"[FAIL] Error: {str(e)[:30]}")
                logger.error(f"Error analyzing job {job.get('job_id', 'unknown')}: {e}")
        
        # Save analyses
        if analyzed:
            analyses_dir = Path(__file__).parent.parent / 'data' / 'analyses'
            analyses_dir.mkdir(parents=True, exist_ok=True)
            
            analyses_file = analyses_dir / f"analyses_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
            with open(analyses_file, 'w', encoding='utf-8') as f:
                for item in analyzed:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
            
            print(f"\n✅ Đã lưu {len(analyzed)} analyses vào {analyses_file.name}")
    
    # Generate daily summary (chỉ nếu có jobs mới)
    if new_jobs:
        print(f"\n📝 Generating daily summary...")
        try:
            daily_summary = generate_daily_summary()
            print(f"✅ Daily summary: {daily_summary.get('total_jobs', 0)} jobs")
            print(f"   Top keywords: {', '.join([k['keyword'] for k in daily_summary.get('top_keywords', [])[:5]])}")
        except Exception as e:
            print(f"✗ Error generating daily summary: {str(e)[:50]}")
    else:
        print(f"\n⏭️  Skipping daily summary (không có jobs mới)")
    
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

