#!/usr/bin/env python3
"""
Script local sync: pull data từ repo, embed và update ChromaDB
Chạy mỗi ngày hoặc khi cần update knowledge base
"""

import os
import sys
import json
import subprocess
import yaml
from pathlib import Path
from datetime import datetime
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load config
config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

chromadb_config = config['chromadb']
raw_jobs_file = Path(__file__).parent.parent / 'data' / 'raw_jobs.jsonl'

def git_pull():
    """Pull data mới từ GitHub repo"""
    try:
        result = subprocess.run(
            ['git', 'pull'],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✓ Git pull thành công")
            return True
        else:
            print(f"⚠ Git pull có vấn đề: {result.stderr}")
            return False
    except Exception as e:
        print(f"⚠ Lỗi git pull: {e}")
        return False

def load_jobs():
    """Load jobs từ raw_jobs.jsonl"""
    jobs = []
    seen_ids = set()
    
    if not raw_jobs_file.exists():
        print("⚠ Không tìm thấy raw_jobs.jsonl")
        return jobs
    
    with open(raw_jobs_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                job = json.loads(line)
                job_id = job.get('job_id', '').strip()
                
                # Validate job
                if not job_id:
                    continue  # Skip jobs without ID
                
                # Skip duplicates trong file
                if job_id in seen_ids:
                    continue
                
                seen_ids.add(job_id)
                jobs.append(job)
            except json.JSONDecodeError as e:
                # Skip invalid JSON lines silently
                continue
            except Exception as e:
                # Only print non-JSON errors
                if "Expecting value" not in str(e):
                    print(f"⚠ Lỗi parse job line {line_num}: {e}")
                continue
    
    print(f"✓ Load được {len(jobs)} jobs (đã loại bỏ duplicate)")
    return jobs

def init_chromadb():
    """Khởi tạo ChromaDB client"""
    persist_dir = Path(__file__).parent.parent / chromadb_config['persist_directory']
    persist_dir.mkdir(parents=True, exist_ok=True)
    
    client = chromadb.PersistentClient(
        path=str(persist_dir),
        settings=Settings(anonymized_telemetry=False)
    )
    
    collection = client.get_or_create_collection(
        name=chromadb_config['collection_name'],
        metadata={"hnsw:space": "cosine"}
    )
    
    return collection

def get_existing_job_ids(collection):
    """Lấy danh sách job_id đã có trong DB"""
    try:
        results = collection.get()
        existing_ids = set(results['ids'])
        return existing_ids
    except:
        return set()

def create_embeddings(texts, model_name='all-MiniLM-L6-v2'):
    """Tạo embeddings cho texts"""
    print(f"✓ Đang tạo embeddings với model {model_name}...")
    model = SentenceTransformer(model_name)
    embeddings = model.encode(texts, show_progress_bar=True)
    return embeddings

def update_chromadb(collection, jobs, existing_ids):
    """Update ChromaDB với jobs mới"""
    # Filter new jobs và loại bỏ duplicate trong batch
    new_jobs = []
    seen_in_batch = set()
    
    for job in jobs:
        job_id = job.get('job_id', '').strip()
        if not job_id:
            continue  # Skip jobs without ID
        
        # Skip nếu đã có trong DB hoặc đã thấy trong batch này
        if job_id in existing_ids or job_id in seen_in_batch:
            continue
        
        seen_in_batch.add(job_id)
        new_jobs.append(job)
    
    if not new_jobs:
        print("✓ Không có job mới cần update")
        return 0
    
    print(f"✓ Tìm thấy {len(new_jobs)} jobs mới (đã loại bỏ duplicate)")
    
    # Tạo text để embed (title + description)
    texts = []
    ids = []
    metadatas = []
    
    for job in new_jobs:
        job_id = job.get('job_id', '').strip()
        if not job_id:
            continue  # Double check
        
        text = f"{job.get('title', '')} {job.get('description', '')}"
        texts.append(text)
        ids.append(job_id)
        
        metadata = {
            'title': job.get('title', '')[:200],  # Limit length
            'budget': str(job.get('budget', '')),
            'proposals': str(job.get('proposals', '')),
            'client_country': job.get('client_country', ''),
            'category': job.get('category', ''),
            'link': job.get('link', ''),
            'source': job.get('source', 'Unknown'),
            'created_at': job.get('created_at', '')
        }
        metadatas.append(metadata)
    
    if not ids:
        print("⚠ Không có jobs hợp lệ để add")
        return 0
    
    # Create embeddings
    embeddings = create_embeddings(texts)
    
    # Add to ChromaDB (batch add để tránh duplicate)
    try:
        collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            metadatas=metadatas,
            documents=texts
        )
        print(f"✓ Đã thêm {len(ids)} jobs vào ChromaDB")
        return len(ids)
    except Exception as e:
        print(f"⚠ Lỗi khi add vào ChromaDB: {e}")
        # Try add từng cái một nếu batch fail
        added = 0
        for i, job_id in enumerate(ids):
            try:
                collection.add(
                    ids=[job_id],
                    embeddings=[embeddings[i].tolist()],
                    metadatas=[metadatas[i]],
                    documents=[texts[i]]
                )
                added += 1
            except:
                continue
        print(f"✓ Đã thêm {added}/{len(ids)} jobs vào ChromaDB (một số có thể duplicate)")
        return added

def main():
    """Main function"""
    print("=" * 50)
    print("🔄 Bắt đầu sync và update ChromaDB...")
    print("=" * 50)
    
    # Step 1: Git pull
    git_pull()
    
    # Step 2: Load jobs
    jobs = load_jobs()
    if not jobs:
        print("⚠ Không có jobs để xử lý")
        return
    
    # Step 3: Init ChromaDB
    collection = init_chromadb()
    existing_ids = get_existing_job_ids(collection)
    print(f"✓ ChromaDB hiện có {len(existing_ids)} jobs")
    
    # Step 4: Update ChromaDB
    new_count = update_chromadb(collection, jobs, existing_ids)
    
    # Step 5: Summary
    print("=" * 50)
    print(f"✅ Hoàn thành! Đã thêm {new_count} jobs mới")
    print(f"📊 Tổng số jobs trong DB: {len(existing_ids) + new_count}")
    print("=" * 50)

if __name__ == '__main__':
    main()

