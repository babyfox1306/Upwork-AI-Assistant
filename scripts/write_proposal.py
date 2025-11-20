#!/usr/bin/env python3
"""
Script viết proposal từ template
Nhận job_id hoặc job link, load job details, fill template và generate proposal
"""

import os
import sys
import yaml
import json
import re
from pathlib import Path
from datetime import datetime
import chromadb
from chromadb.config import Settings
try:
    from ollama import Client
    OLLAMA_CLIENT = True
except ImportError:
    try:
        import ollama
        OLLAMA_CLIENT = False
    except ImportError:
        print("⚠ Lỗi: Không tìm thấy ollama. Hãy cài: pip install ollama")
        sys.exit(1)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load config
config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
profile_path = Path(__file__).parent.parent / 'config' / 'profile.yaml'
template_path = Path(__file__).parent.parent / 'config' / 'proposal_template.txt'

with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

with open(profile_path, 'r', encoding='utf-8') as f:
    profile = yaml.safe_load(f)

with open(template_path, 'r', encoding='utf-8') as f:
    template = f.read()

chromadb_config = config['chromadb']
ollama_config = config['ollama']
proposals_dir = Path(__file__).parent.parent / 'data' / 'proposals'
proposals_dir.mkdir(parents=True, exist_ok=True)

def init_chromadb():
    """Khởi tạo ChromaDB client"""
    persist_dir = Path(__file__).parent.parent / chromadb_config['persist_directory']
    
    client = chromadb.PersistentClient(
        path=str(persist_dir),
        settings=Settings(anonymized_telemetry=False)
    )
    
    collection = client.get_collection(chromadb_config['collection_name'])
    return collection

def load_job_from_jsonl(job_id):
    """Load job từ raw_jobs.jsonl"""
    raw_jobs_file = Path(__file__).parent.parent / 'data' / 'raw_jobs.jsonl'
    
    if not raw_jobs_file.exists():
        return None
    
    with open(raw_jobs_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    job = json.loads(line)
                    if job.get('job_id') == job_id:
                        return job
                except:
                    continue
    
    return None

def load_job_from_chromadb(collection, job_id):
    """Load job từ ChromaDB"""
    try:
        results = collection.get(ids=[job_id])
        if results['ids']:
            metadata = results['metadatas'][0]
            documents = results['documents'][0] if results['documents'] else ''
            
            job = {
                'job_id': job_id,
                'title': metadata.get('title', ''),
                'description': documents,
                'budget': metadata.get('budget', ''),
                'proposals': metadata.get('proposals', ''),
                'client_country': metadata.get('client_country', ''),
                'category': metadata.get('category', ''),
                'link': metadata.get('link', ''),
                'created_at': metadata.get('created_at', '')
            }
            return job
    except:
        pass
    
    return None

def extract_job_id_from_link(link):
    """Extract job_id từ Upwork link"""
    match = re.search(r'/jobs/~([a-f0-9]+)', link)
    if match:
        return match.group(1)
    return None

def extract_client_name(job_description):
    """Extract client name từ job description (nếu có)"""
    # Thường có format "Hi, I'm [Name]" hoặc "My name is [Name]"
    name_match = re.search(r"(?:hi|hello|my name is|i'm|i am)\s+([A-Z][a-z]+)", job_description, re.IGNORECASE)
    if name_match:
        return name_match.group(1)
    return "Client"

def summarize_job(job_description):
    """Tóm tắt job description"""
    # Lấy 2-3 câu đầu làm summary
    sentences = re.split(r'[.!?]+', job_description)
    summary = '. '.join(sentences[:3]).strip()
    if len(summary) > 200:
        summary = summary[:200] + '...'
    return summary

def build_proposal_prompt(job, profile, template):
    """Build prompt để generate proposal"""
    
    client_name = extract_client_name(job.get('description', ''))
    job_summary = summarize_job(job.get('description', ''))
    skills_text = ', '.join(profile.get('skills', []))
    
    prompt = f"""Em là Upwork Assistant của CEO Hùng. Em cần viết proposal cho job này.

Job Details:
- Title: {job.get('title', '')}
- Description: {job.get('description', '')[:1000]}
- Budget: {job.get('budget', 'N/A')}
- Client: {job.get('client_country', 'Unknown')}

Profile CEO:
- Skills: {skills_text}
- Experience: {profile.get('experience', 0)} năm
- Rate: {profile.get('rate', '')}
- Portfolio: {profile.get('portfolio', [])}

Template Proposal:
{template}

Nhiệm vụ:
1. Fill template với thông tin job và profile
2. Thay [Client Name] bằng "{client_name}" hoặc "Client" nếu không tìm thấy
3. Thay [skills] bằng skills phù hợp với job
4. Thay [Job Summary] bằng tóm tắt ngắn gọn job
5. Giữ nguyên [CÁ NHÂN HÓA] - đây là placeholder để CEO tự điền sau
6. Đảm bảo proposal 150-200 từ
7. Giọng điệu: thân thiện, chuyên nghiệp, freelancer VN 8-10 năm kinh nghiệm
8. KHÔNG dùng từ "nên", "phải", "tốt nhất", "đề xuất"

Hãy viết proposal hoàn chỉnh theo template trên."""

    return prompt

def generate_proposal(prompt):
    """Generate proposal từ Ollama"""
    try:
        base_url = ollama_config.get('base_url', 'http://localhost:11434')
        
        if OLLAMA_CLIENT:
            client = Client(host=base_url)
            response = client.chat(
                model=ollama_config['model'],
                messages=[
                    {
                        'role': 'system',
                        'content': 'Em là Upwork Assistant của CEO Hùng. Em viết proposal chuyên nghiệp, thân thiện, dựa trên template và thông tin job.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            )
            return response['message']['content']
        else:
            response = ollama.chat(
                model=ollama_config['model'],
                messages=[
                    {
                        'role': 'system',
                        'content': 'Em là Upwork Assistant của CEO Hùng. Em viết proposal chuyên nghiệp, thân thiện, dựa trên template và thông tin job.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            )
            return response['message']['content']
    except Exception as e:
        return f"Lỗi khi generate proposal: {e}. Đảm bảo Ollama đang chạy: ollama serve"

def save_proposal(job_id, proposal_text, job_link):
    """Lưu proposal vào data/proposals/"""
    proposal_file = proposals_dir / f"{job_id}.jsonl"
    
    proposal_data = {
        'job_id': job_id,
        'job_link': job_link,
        'proposal_text': proposal_text,
        'created_at': datetime.utcnow().isoformat(),
        'success_flag': None  # CEO có thể update sau
    }
    
    with open(proposal_file, 'w', encoding='utf-8') as f:
        f.write(json.dumps(proposal_data, ensure_ascii=False) + '\n')
    
    print(f"✓ Đã lưu proposal vào {proposal_file}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate proposal cho Upwork job')
    parser.add_argument('job_id', type=str, help='Job ID hoặc job link')
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("✍️  Đang generate proposal...")
    print("=" * 50)
    
    # Extract job_id
    job_id = args.job_id
    if job_id.startswith('http'):
        job_id = extract_job_id_from_link(job_id)
        if not job_id:
            print("⚠ Không thể extract job_id từ link")
            return
    
    # Load job
    collection = init_chromadb()
    job = load_job_from_chromadb(collection, job_id)
    
    if not job:
        job = load_job_from_jsonl(job_id)
    
    if not job:
        print(f"⚠ Không tìm thấy job với ID: {job_id}")
        return
    
    print(f"✓ Đã load job: {job.get('title', '')}")
    
    # Build prompt
    prompt = build_proposal_prompt(job, profile, template)
    
    # Generate proposal
    print("✓ Đang generate proposal với Ollama...")
    proposal = generate_proposal(prompt)
    
    # Output
    print("\n" + "=" * 50)
    print("PROPOSAL:")
    print("=" * 50)
    print(proposal)
    print("=" * 50)
    
    # Save proposal
    save_proposal(job_id, proposal, job.get('link', ''))
    
    print("\n✓ Hoàn thành! Proposal đã được lưu.")

if __name__ == '__main__':
    main()

