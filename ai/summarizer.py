#!/usr/bin/env python3
"""
AI Trend Summarizer - Tóm tắt trend hàng ngày/tuần từ feeds
"""

import yaml
import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime, timedelta
from collections import Counter
import ollama

# Load config
config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

ollama_config = config.get('ollama', {})
ollama_model = ollama_config.get('model', 'qwen2.5:7b-instruct-q4_K_M')

def load_jobs_from_period(days: int = 1) -> List[Dict]:
    """Load jobs từ N ngày gần đây"""
    jobs_file = Path(__file__).parent.parent / 'data' / 'raw_jobs.jsonl'
    if not jobs_file.exists():
        return []
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    jobs = []
    
    with open(jobs_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    job = json.loads(line)
                    created_at = job.get('created_at', '')
                    if created_at:
                        try:
                            job_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            if job_date >= cutoff_date:
                                jobs.append(job)
                        except:
                            pass
                except:
                    pass
    
    return jobs

def extract_top_keywords(jobs: List[Dict], top_n: int = 10) -> List[tuple]:
    """Extract top keywords từ jobs"""
    all_text = ' '.join([
        f"{j.get('title', '')} {j.get('description', '')}" 
        for j in jobs
    ]).lower()
    
    # Common tech keywords
    tech_keywords = [
        'python', 'javascript', 'react', 'node.js', 'laravel', 'wordpress',
        'api', 'automation', 'scraping', 'ai', 'machine learning', 'ml',
        'data processing', 'e-commerce', 'shopify', 'full stack',
        'frontend', 'backend', 'typescript', 'vue', 'angular',
        'docker', 'kubernetes', 'aws', 'cloud', 'devops'
    ]
    
    keyword_counts = Counter()
    for keyword in tech_keywords:
        count = all_text.count(keyword)
        if count > 0:
            keyword_counts[keyword] = count
    
    return keyword_counts.most_common(top_n)

def generate_daily_summary() -> Dict:
    """Generate daily summary"""
    jobs = load_jobs_from_period(days=1)
    
    if not jobs:
        return {
            'date': datetime.utcnow().isoformat(),
            'total_jobs': 0,
            'summary': 'Không có job mới hôm nay',
            'top_keywords': [],
            'top_categories': []
        }
    
    # Top keywords
    top_keywords = extract_top_keywords(jobs, top_n=10)
    
    # Top categories
    categories = Counter([j.get('category', 'General') for j in jobs])
    top_categories = categories.most_common(5)
    
    # Top sources
    sources = Counter([j.get('source', 'Unknown') for j in jobs])
    top_sources = sources.most_common(3)
    
    # Generate AI summary
    jobs_sample = jobs[:10]  # Lấy 10 jobs đầu để summarize
    jobs_text = '\n'.join([
        f"- {j.get('title', 'N/A')} ({j.get('source', 'N/A')})"
        for j in jobs_sample
    ])
    
    prompt = f"""Bạn là Lysa - AI phân tích trend job market.

Hôm nay có {len(jobs)} jobs mới từ {len(set(j.get('source') for j in jobs))} nguồn.

Top keywords: {', '.join([k[0] for k in top_keywords[:5]])}
Top categories: {', '.join([c[0] for c in top_categories])}

Mẫu jobs:
{jobs_text}

Hãy tóm tắt trend hôm nay trong 3-5 câu:
- Job nào đang hot?
- Skill nào đang được tìm nhiều?
- Budget trend như thế nào?
- Có pattern gì đáng chú ý không?

Trả lời ngắn gọn, thực tế, không vòng vo."""

    try:
        response = ollama.chat(
            model=ollama_model,
            messages=[
                {
                    'role': 'system',
                    'content': 'Bạn là Lysa - AI phân tích trend job market, thực tế, ngắn gọn.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        )
        
        summary_text = response['message']['content']
    except Exception as e:
        summary_text = f"Lỗi generate summary: {str(e)}"
    
    result = {
        'date': datetime.utcnow().isoformat(),
        'total_jobs': len(jobs),
        'summary': summary_text,
        'top_keywords': [{'keyword': k[0], 'count': k[1]} for k in top_keywords],
        'top_categories': [{'category': c[0], 'count': c[1]} for c in top_categories],
        'top_sources': [{'source': s[0], 'count': s[1]} for s in top_sources]
    }
    
    # Save summary
    trends_dir = Path(__file__).parent.parent / 'data' / 'trends'
    trends_dir.mkdir(parents=True, exist_ok=True)
    
    summary_file = trends_dir / f"daily_summary_{datetime.utcnow().strftime('%Y%m%d')}.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    return result

def generate_weekly_summary() -> Dict:
    """Generate weekly summary"""
    jobs = load_jobs_from_period(days=7)
    
    if not jobs:
        return {
            'week_start': (datetime.utcnow() - timedelta(days=7)).isoformat(),
            'week_end': datetime.utcnow().isoformat(),
            'total_jobs': 0,
            'summary': 'Không có job trong tuần này'
        }
    
    # Similar to daily but aggregate over 7 days
    top_keywords = extract_top_keywords(jobs, top_n=15)
    categories = Counter([j.get('category', 'General') for j in jobs])
    top_categories = categories.most_common(10)
    
    prompt = f"""Bạn là Lysa - AI phân tích trend job market.

Tuần này có {len(jobs)} jobs từ {len(set(j.get('source') for j in jobs))} nguồn.

Top keywords tuần: {', '.join([k[0] for k in top_keywords[:10]])}
Top categories: {', '.join([c[0] for c in top_categories[:5]])}

Hãy tóm tắt trend tuần này:
- Job nào tăng/giảm?
- Skill nào đang lên trend?
- Pattern gì đáng chú ý?
- Insight cho freelancer?

Trả lời 5-7 câu, thực tế, có insight."""

    try:
        response = ollama.chat(
            model=ollama_model,
            messages=[
                {
                    'role': 'system',
                    'content': 'Bạn là Lysa - AI phân tích trend job market tuần, thực tế, có insight.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        )
        
        summary_text = response['message']['content']
    except Exception as e:
        summary_text = f"Lỗi generate summary: {str(e)}"
    
    result = {
        'week_start': (datetime.utcnow() - timedelta(days=7)).isoformat(),
        'week_end': datetime.utcnow().isoformat(),
        'total_jobs': len(jobs),
        'summary': summary_text,
        'top_keywords': [{'keyword': k[0], 'count': k[1]} for k in top_keywords],
        'top_categories': [{'category': c[0], 'count': c[1]} for c in top_categories]
    }
    
    # Save summary
    trends_dir = Path(__file__).parent.parent / 'data' / 'trends'
    trends_dir.mkdir(parents=True, exist_ok=True)
    
    week_num = datetime.utcnow().isocalendar()[1]
    summary_file = trends_dir / f"weekly_summary_{datetime.utcnow().year}_W{week_num}.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    return result

if __name__ == '__main__':
    # Test daily summary
    print("Generating daily summary...")
    daily = generate_daily_summary()
    print(json.dumps(daily, ensure_ascii=False, indent=2))
    
    # Test weekly summary
    print("\nGenerating weekly summary...")
    weekly = generate_weekly_summary()
    print(json.dumps(weekly, ensure_ascii=False, indent=2))

