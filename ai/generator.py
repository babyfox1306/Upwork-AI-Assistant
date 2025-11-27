#!/usr/bin/env python3
"""
AI Proposal Generator - Generate proposal draft từ template
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Optional
import ollama

# Load config
config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

ollama_config = config.get('ollama', {})
ollama_model = ollama_config.get('model', 'qwen2.5:7b-instruct-q4_K_M')
ollama_base_url = ollama_config.get('base_url', 'http://localhost:11434')

# Load AI rules
ai_rules_path = Path(__file__).parent.parent / 'ai_rules'
profile_context = (ai_rules_path / 'profile_context.md').read_text(encoding='utf-8') if (ai_rules_path / 'profile_context.md').exists() else ""

def load_profile():
    """Load freelancer profile (Tuấn Anh)"""
    profile_path = Path(__file__).parent.parent / 'config' / 'profile.yaml'
    if profile_path.exists():
        with open(profile_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}

def load_template() -> str:
    """Load proposal template"""
    template_path = Path(__file__).parent.parent / 'config' / 'proposal_template.txt'
    if template_path.exists():
        return template_path.read_text(encoding='utf-8')
    return """Hi [CLIENT_NAME],

I saw your job posting for [JOB_TITLE] and I'm interested.

[CÁ NHÂN HÓA - Explain why you're a good fit]

I have experience with [RELEVANT_SKILLS].

Let me know if you'd like to discuss further.

Best regards,
[YOUR_NAME]
"""

def find_job(job_id: str = None, job_link: str = None) -> Optional[Dict]:
    """Find job từ job_id hoặc job_link"""
    jobs_file = Path(__file__).parent.parent / 'data' / 'raw_jobs.jsonl'
    if not jobs_file.exists():
        return None
    
    with open(jobs_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    job = json.loads(line)
                    if job_id and job.get('job_id') == job_id:
                        return job
                    if job_link and job.get('link') == job_link:
                        return job
                except:
                    pass
    
    return None

def generate_proposal(job_id: str = None, job_link: str = None, job_data: Dict = None) -> Dict:
    """
    Generate proposal draft từ job
    """
    # Load job data
    if not job_data:
        if job_id:
            job_data = find_job(job_id=job_id)
        elif job_link:
            job_data = find_job(job_link=job_link)
        else:
            return {'error': 'Cần job_id, job_link hoặc job_data'}
    
    if not job_data:
        return {'error': 'Không tìm thấy job'}
    
    # Load profile và template
    profile = load_profile()
    template = load_template()
    
    # Build prompt với creativity và không rập khuôn
    prompt = f"""Bạn là Lysa - AI hỗ trợ viết proposal chuyên nghiệp, sáng tạo, không rập khuôn. Bạn hỗ trợ Tuấn Anh (freelancer).

CÁCH VIẾT PROPOSAL:
- Linh hoạt: mỗi proposal khác nhau, phù hợp với từng job cụ thể
- Tự nhiên: không dùng template cứng nhắc, viết như đang nói chuyện với client
- Cá nhân hóa: highlight điểm phù hợp nhất với job này, không list tất cả skills
- Sáng tạo: thay đổi cách mở đầu, cách kết thúc, cách trình bày
- Thực tế: nói về value cụ thể, không chỉ list features
- Không rập khuôn: tránh dùng cùng một cấu trúc, cùng một từ ngữ cho mọi proposal

{profile_context}

PROFILE FREELANCER (Tuấn Anh - freelancer thật):
{json.dumps(profile, ensure_ascii=False, indent=2)}

QUAN TRỌNG: Profile trên là của Tuấn Anh (freelancer thật), không phải "CEO Lysa". Bạn phải generate proposals dựa trên skills/work style thực tế của Tuấn Anh. Nhấn mạnh demo-first approach.

JOB CẦN VIẾT PROPOSAL:
Title: {job_data.get('title', 'N/A')}
Description: {job_data.get('description', 'N/A')[:1500]}
Budget: {job_data.get('budget', 'N/A')}
Source: {job_data.get('source', 'N/A')}

TEMPLATE:
{template}

YÊU CẦU:
1. Fill template với thông tin job và profile, nhưng LINH HOẠT - không rập khuôn
2. Thay [CÁ NHÂN HÓA] bằng đoạn giải thích tại sao phù hợp (2-3 câu), mỗi job khác nhau thì viết khác nhau
3. Thay [RELEVANT_SKILLS] bằng skills liên quan từ profile, nhưng chỉ highlight những gì THỰC SỰ liên quan
4. Tone tự nhiên: như đang nói chuyện với client, không quá formal, không quá casual
5. Độ dài 150-200 từ, nhưng có thể linh hoạt
6. Tập trung vào VALUE cụ thể cho job này, không chỉ list skills chung chung
7. Tránh salesy: không dùng "I am the best", "I guarantee", "I promise"
8. Sáng tạo: thay đổi cách mở đầu, cách kết thúc, cách trình bày cho mỗi proposal
9. Cá nhân hóa: mỗi proposal phải khác nhau, phù hợp với từng job cụ thể

VÍ DỤ KHÔNG RẬP KHUÔN:
- Job A: Mở đầu bằng câu hỏi hoặc observation về project
- Job B: Mở đầu bằng kinh nghiệm tương tự
- Job C: Mở đầu bằng cách tiếp cận cụ thể

Trả lời CHỈ proposal text, không thêm gì khác."""

    try:
        from ollama import Client
        client = Client(host=ollama_base_url, timeout=60.0)
        
        response = client.chat(
            model=ollama_model,
            messages=[
                {
                    'role': 'system',
                    'content': 'Bạn là Lysa - AI viết proposal chuyên nghiệp, sáng tạo, không rập khuôn, thực tế, không salesy. Mỗi proposal phải khác nhau, phù hợp với từng job cụ thể.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            options={
                'temperature': 0.8,  # Tăng temperature để sáng tạo hơn, không rập khuôn
                'num_predict': 500,
                'top_p': 0.9,  # Diversity trong cách viết
            }
        )
        
        proposal_text = response['message']['content'].strip()
        
        # Save proposal
        proposals_dir = Path(__file__).parent.parent / 'data' / 'proposals'
        proposals_dir.mkdir(parents=True, exist_ok=True)
        
        proposal_data = {
            'job_id': job_data.get('job_id'),
            'job_title': job_data.get('title'),
            'job_link': job_data.get('link'),
            'proposal': proposal_text,
            'generated_at': __import__('datetime').datetime.utcnow().isoformat(),
            'template_used': True
        }
        
        proposal_file = proposals_dir / f"proposal_{job_data.get('job_id', 'unknown')}.json"
        with open(proposal_file, 'w', encoding='utf-8') as f:
            json.dump(proposal_data, f, ensure_ascii=False, indent=2)
        
        return proposal_data
        
    except Exception as e:
        return {
            'error': str(e),
            'job_id': job_data.get('job_id')
        }

if __name__ == '__main__':
    # Test với job mẫu
    test_job = {
        'job_id': 'test123',
        'title': 'Python Web Scraping Project',
        'description': 'Need Python developer to scrape data from websites. Budget $500.',
        'budget': '$500',
        'source': 'RemoteOK',
        'link': 'https://example.com'
    }
    
    result = generate_proposal(job_data=test_job)
    print(json.dumps(result, ensure_ascii=False, indent=2))

