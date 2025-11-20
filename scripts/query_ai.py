#!/usr/bin/env python3
"""
Script query AI để phân tích job và liệt kê jobs match
Sử dụng prompt engineering kỷ luật: AI chỉ là trợ lý, CEO chốt
"""

import os
import sys
import yaml
from pathlib import Path
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
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

with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

with open(profile_path, 'r', encoding='utf-8') as f:
    profile = yaml.safe_load(f)

chromadb_config = config['chromadb']
ollama_config = config['ollama']
query_config = config['query']

def init_chromadb():
    """Khởi tạo ChromaDB client"""
    persist_dir = Path(__file__).parent.parent / chromadb_config['persist_directory']
    
    client = chromadb.PersistentClient(
        path=str(persist_dir),
        settings=Settings(anonymized_telemetry=False)
    )
    
    collection = client.get_collection(chromadb_config['collection_name'])
    return collection

def search_jobs(collection, query_text, top_k=10):
    """Search jobs trong ChromaDB"""
    # Tạo embedding cho query
    model = SentenceTransformer('all-MiniLM-L6-v2')
    query_embedding = model.encode([query_text])[0].tolist()
    
    # Query ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    
    jobs = []
    if results['ids'] and len(results['ids'][0]) > 0:
        for i in range(len(results['ids'][0])):
            job = {
                'job_id': results['ids'][0][i],
                'title': results['metadatas'][0][i].get('title', ''),
                'description': results['documents'][0][i],
                'budget': results['metadatas'][0][i].get('budget', ''),
                'proposals': results['metadatas'][0][i].get('proposals', ''),
                'client_country': results['metadatas'][0][i].get('client_country', ''),
                'category': results['metadatas'][0][i].get('category', ''),
                'link': results['metadatas'][0][i].get('link', ''),
                'created_at': results['metadatas'][0][i].get('created_at', ''),
                'distance': results['distances'][0][i] if results.get('distances') else None
            }
            jobs.append(job)
    
    return jobs

def detect_scam_flags(job):
    """Phát hiện dấu hiệu scam từ job description"""
    description = job.get('description', '').lower()
    flags = []
    
    scam_patterns = [
        ('release milestone after complete all', 'Yêu cầu release milestone sau khi hoàn thành tất cả'),
        ('hourly giả fixed', 'Budget fixed nhưng yêu cầu hourly'),
        ('upfront payment required', 'Yêu cầu thanh toán trước'),
        ('send your password', 'Yêu cầu gửi password'),
        ('click this link', 'Yêu cầu click link lạ'),
        ('western union', 'Thanh toán qua Western Union'),
        ('moneygram', 'Thanh toán qua MoneyGram'),
        ('urgent need', 'Cần gấp + budget thấp'),
    ]
    
    for pattern, flag_text in scam_patterns:
        if pattern in description:
            flags.append(flag_text)
    
    if len(flags) == 0:
        return "Không phát hiện dấu hiệu scam"
    
    return "; ".join(flags[:3])  # Tối đa 3 flags

def estimate_win_rate(job, profile):
    """Ước lượng tỉ lệ thắng dựa trên match skills và proposals"""
    proposals = int(job.get('proposals', 0) or 0)
    budget = job.get('budget', '')
    
    # Match skills
    job_desc = job.get('description', '').lower()
    profile_skills = [s.lower() for s in profile.get('skills', [])]
    skill_matches = sum(1 for skill in profile_skills if skill in job_desc)
    
    # Tính điểm match
    match_score = 0
    
    # Skills match (0-5 điểm)
    match_score += min(skill_matches * 2, 5)
    
    # Proposals (càng ít càng tốt)
    if proposals < 5:
        match_score += 3
    elif proposals < 15:
        match_score += 2
    elif proposals < 25:
        match_score += 1
    
    # Budget (có budget tốt hơn không có)
    if budget:
        match_score += 1
    
    # Ước lượng
    if match_score >= 7:
        return "Cao (>50%)"
    elif match_score >= 4:
        return "Trung bình (30-50%)"
    else:
        return "Thấp (<30%)"

def find_match_strengths(job, profile):
    """Tìm 3 điểm mạnh match với job"""
    job_desc = job.get('description', '').lower()
    profile_skills = profile.get('skills', [])
    experience = profile.get('experience', 0)
    
    strengths = []
    
    # Match skills
    matched_skills = [s for s in profile_skills if s.lower() in job_desc]
    if matched_skills:
        strengths.append(f"Skills match: {', '.join(matched_skills[:3])}")
    
    # Experience
    if experience >= 8:
        strengths.append(f"Có {experience} năm kinh nghiệm, phù hợp với job này")
    
    # Portfolio
    portfolio = profile.get('portfolio', [])
    if portfolio:
        strengths.append(f"Có portfolio tương tự: {portfolio[0].get('description', '')}")
    
    # Budget match
    budget = job.get('budget', '')
    rate = profile.get('rate', '')
    if budget and rate:
        strengths.append(f"Budget {budget} phù hợp với rate {rate}")
    
    return strengths[:3]  # Tối đa 3 điểm

def find_customization_points(job, profile):
    """Tìm 3 điểm cần cá nhân hóa proposal"""
    points = []
    
    # Hỏi thêm về tech stack
    job_desc = job.get('description', '').lower()
    if 'payment' in job_desc or 'gateway' in job_desc:
        points.append("Hỏi thêm về Stripe hay PayPal, mention dự án cũ tương tự")
    
    # Mention experience tương tự
    if profile.get('experience', 0) >= 8:
        points.append(f"Mention {profile.get('experience')} năm kinh nghiệm với dự án tương tự")
    
    # Portfolio reference
    portfolio = profile.get('portfolio', [])
    if portfolio:
        points.append(f"Reference portfolio project: {portfolio[0].get('link', '')}")
    
    # Budget negotiation
    budget = job.get('budget', '')
    if budget:
        points.append(f"Confirm budget {budget} và timeline cụ thể")
    
    return points[:3]  # Tối đa 3 điểm

def load_ai_rules():
    """Load AI rules từ ai_rules/"""
    rules_dir = Path(__file__).parent.parent / 'ai_rules'
    rules = {}
    
    # Load system instruction
    analysis_file = rules_dir / 'analysis.md'
    if analysis_file.exists():
        with open(analysis_file, 'r', encoding='utf-8') as f:
            rules['system'] = f.read()
    
    # Load rulebook
    rules_file = rules_dir / 'upwork_rules.md'
    if rules_file.exists():
        with open(rules_file, 'r', encoding='utf-8') as f:
            rules['rulebook'] = f.read()
    
    # Load hardware constraints
    hardware_file = rules_dir / 'hardware.md'
    if hardware_file.exists():
        with open(hardware_file, 'r', encoding='utf-8') as f:
            rules['hardware'] = f.read()
    
    return rules

def build_prompt(jobs, profile):
    """Build prompt cho Ollama với quy tắc kỷ luật"""
    
    # Load AI rules
    ai_rules = load_ai_rules()
    
    profile_text = f"""
Profile CEO:
- Skills: {', '.join(profile.get('skills', []))}
- Experience: {profile.get('experience', 0)} năm
- Rate: {profile.get('rate', '')}
"""
    
    jobs_text = ""
    for i, job in enumerate(jobs, 1):
        jobs_text += f"""
Job {i}:
- Title: {job.get('title', '')}
- Description: {job.get('description', '')[:500]}
- Budget: {job.get('budget', 'N/A')}
- Proposals: {job.get('proposals', 'N/A')}
- Client: {job.get('client_country', 'Unknown')}
- Link: {job.get('link', '')}
"""
    
    # Build system prompt với AI rules
    system_instruction = ai_rules.get('system', '')
    rulebook = ai_rules.get('rulebook', '')
    hardware = ai_rules.get('hardware', '')
    
    prompt = f"""{system_instruction}

{rulebook}

{hardware}

{profile_text}

Em vừa scan được {len(jobs)} jobs. Hãy phân tích từng job theo đúng 7 TẦNG trong RULEBOOK:

{jobs_text}

PHÂN TÍCH BẮT BUỘC THEO 7 TẦNG:
1) INTENT ANALYSIS - Lý do khách post job
2) TECH FEASIBILITY - Có gì không thực tế?
3) SCOPE CREEP DETECTION - Mùi phình scope
4) ROI CHECK REAL - Lời bao nhiêu theo giờ?
5) COMPETITION INTEL - Số proposal, dân Ấn/Pakistan, cheap labor trap
6) TIER MATCHING - Job này hợp với mình không?
7) VERDICT - CHỐT: NÊN LẤY / KHÔNG NÊN LẤY (có lý do chiến lược)

Tuân thủ 100%: nói thẳng như chiến binh Gen Z, thực tế, quyết đoán, không vòng vo, không chung chung."""
    
    return prompt

def query_ollama(prompt):
    """Query Ollama với prompt"""
    try:
        base_url = ollama_config.get('base_url', 'http://localhost:11434')
        
        if OLLAMA_CLIENT:
            client = Client(host=base_url)
            response = client.chat(
                model=ollama_config['model'],
                messages=[
                    {
                        'role': 'system',
                        'content': 'Em là Upwork Assistant của CEO Hùng. Em chỉ phân tích và liệt kê, không quyết định. Luôn dùng ngôi "em" và giọng điệu thực tế, hơi bựa.'
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
                        'content': 'Em là Upwork Assistant của CEO Hùng. Em chỉ phân tích và liệt kê, không quyết định. Luôn dùng ngôi "em" và giọng điệu thực tế, hơi bựa.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            )
            return response['message']['content']
    except Exception as e:
        return f"Lỗi khi query Ollama: {e}. Đảm bảo Ollama đang chạy: ollama serve"

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Query AI để phân tích Upwork jobs')
    parser.add_argument('--query', type=str, default='', help='Query text để search jobs (optional)')
    parser.add_argument('--top-k', type=int, default=query_config['top_k'], help='Số lượng jobs trả về')
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("🔍 Đang query AI phân tích jobs...")
    print("=" * 50)
    
    # Init ChromaDB
    collection = init_chromadb()
    
    # Search jobs
    if args.query:
        query_text = args.query
    else:
        # Default: search với skills của profile
        query_text = f"{', '.join(profile.get('skills', []))} freelancer"
    
    jobs = search_jobs(collection, query_text, top_k=args.top_k)
    
    if not jobs:
        print("⚠ Không tìm thấy jobs nào")
        return
    
    print(f"✓ Tìm thấy {len(jobs)} jobs")
    
    # Build prompt với jobs đã được phân tích sơ bộ
    # Thêm thông tin scam flag, win rate, match strengths vào prompt
    enriched_jobs = []
    for job in jobs:
        job['scam_flag'] = detect_scam_flags(job)
        job['win_rate'] = estimate_win_rate(job, profile)
        job['match_strengths'] = find_match_strengths(job, profile)
        job['customization_points'] = find_customization_points(job, profile)
        enriched_jobs.append(job)
    
    # Query Ollama
    prompt = build_prompt(enriched_jobs, profile)
    response = query_ollama(prompt)
    
    # Output
    print("\n" + "=" * 50)
    print(response)
    print("=" * 50)

if __name__ == '__main__':
    main()

