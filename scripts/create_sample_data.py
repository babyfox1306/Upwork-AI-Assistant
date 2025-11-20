#!/usr/bin/env python3
"""
Script tạo sample data để test hệ thống
Dùng khi chưa có Upwork API key hoặc muốn test local
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

sample_jobs = [
    {
        'job_id': 'sample001',
        'title': 'WordPress Developer Needed for E-commerce Site',
        'description': 'Looking for an experienced WordPress developer to build an e-commerce site with WooCommerce. Must have experience with payment gateways and custom plugins. Budget: $1,200 fixed. Client from USA.',
        'link': 'https://www.upwork.com/jobs/~sample001',
        'budget': '1200',
        'proposals': '8',
        'client_country': 'USA',
        'category': 'WordPress',
        'created_at': (datetime.utcnow() - timedelta(hours=2)).isoformat(),
        'crawled_at': datetime.utcnow().isoformat()
    },
    {
        'job_id': 'sample002',
        'title': 'Laravel API Development - Payment Integration',
        'description': 'Need Laravel developer to build REST API with Stripe payment integration. Experience with Laravel 10+, API development, and payment gateways required. Budget: $1,500 fixed. Client from Canada.',
        'link': 'https://www.upwork.com/jobs/~sample002',
        'budget': '1500',
        'proposals': '12',
        'client_country': 'Canada',
        'category': 'Laravel',
        'created_at': (datetime.utcnow() - timedelta(hours=5)).isoformat(),
        'crawled_at': datetime.utcnow().isoformat()
    },
    {
        'job_id': 'sample003',
        'title': 'Shopify Store Setup and Customization',
        'description': 'Looking for Shopify expert to set up new store and customize theme. Need help with product import, payment setup, and basic customization. Budget: $800 fixed. Client from UK.',
        'link': 'https://www.upwork.com/jobs/~sample003',
        'budget': '800',
        'proposals': '15',
        'client_country': 'UK',
        'category': 'Shopify',
        'created_at': (datetime.utcnow() - timedelta(hours=1)).isoformat(),
        'crawled_at': datetime.utcnow().isoformat()
    },
    {
        'job_id': 'sample004',
        'title': 'Node.js Backend Developer - Real-time Chat App',
        'description': 'Need Node.js developer to build backend for real-time chat application. Experience with Socket.io, Express, MongoDB required. Budget: $2,000 fixed. Client from USA.',
        'link': 'https://www.upwork.com/jobs/~sample004',
        'budget': '2000',
        'proposals': '6',
        'client_country': 'USA',
        'category': 'Node.js',
        'created_at': (datetime.utcnow() - timedelta(hours=3)).isoformat(),
        'crawled_at': datetime.utcnow().isoformat()
    },
    {
        'job_id': 'sample005',
        'title': 'React Developer - Dashboard UI',
        'description': 'Looking for React developer to build admin dashboard. Must have experience with React, TypeScript, and Material-UI. Budget: $1,000 fixed. Client from Germany.',
        'link': 'https://www.upwork.com/jobs/~sample005',
        'budget': '1000',
        'proposals': '20',
        'client_country': 'Germany',
        'category': 'React',
        'created_at': (datetime.utcnow() - timedelta(hours=4)).isoformat(),
        'crawled_at': datetime.utcnow().isoformat()
    },
    {
        'job_id': 'sample006',
        'title': 'Web Scraping - Product Data Extraction',
        'description': 'Need Python developer to scrape product data from e-commerce sites. Must handle anti-scraping measures and export to CSV. Budget: $600 fixed. Client from India.',
        'link': 'https://www.upwork.com/jobs/~sample006',
        'budget': '600',
        'proposals': '25',
        'client_country': 'India',
        'category': 'Web Scraping',
        'created_at': (datetime.utcnow() - timedelta(hours=6)).isoformat(),
        'crawled_at': datetime.utcnow().isoformat()
    }
]

def main():
    """Tạo sample data file"""
    raw_jobs_file = Path(__file__).parent.parent / 'data' / 'raw_jobs.jsonl'
    
    # Tạo file nếu chưa có
    raw_jobs_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Append sample jobs
    with open(raw_jobs_file, 'a', encoding='utf-8') as f:
        for job in sample_jobs:
            f.write(json.dumps(job, ensure_ascii=False) + '\n')
    
    print(f"✅ Đã tạo {len(sample_jobs)} sample jobs vào {raw_jobs_file}")
    print("💡 Bây giờ bạn có thể chạy: python scripts/local_sync_and_rag.py")

if __name__ == '__main__':
    main()

