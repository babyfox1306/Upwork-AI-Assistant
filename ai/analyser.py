#!/usr/bin/env python3
"""
AI Job Analyser - Phân tích job, scoring, category detection, trend extraction
"""

import yaml
import json
import sys
from pathlib import Path
from typing import Dict, List
# ollama không dùng trực tiếp nữa, dùng Client

# Add parent directory to path for utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import setup_logger

# Setup logger
logger = setup_logger('ai_analyser')

# Load config
config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

ollama_config = config.get('ollama', {})
ollama_model = ollama_config.get('model', 'qwen2.5:7b-instruct-q4_K_M')
ollama_base_url = ollama_config.get('base_url', 'http://localhost:11434')

# Load AI rules
ai_rules_path = Path(__file__).parent.parent / 'ai_rules'
analysis_rules = (ai_rules_path / 'analysis.md').read_text(encoding='utf-8')
upwork_rules = (ai_rules_path / 'upwork_rules.md').read_text(encoding='utf-8')
hardware_rules = (ai_rules_path / 'hardware.md').read_text(encoding='utf-8')
profile_context = (ai_rules_path / 'profile_context.md').read_text(encoding='utf-8') if (ai_rules_path / 'profile_context.md').exists() else ""

def load_profile():
    """Load CEO profile"""
    profile_path = Path(__file__).parent.parent / 'config' / 'profile.yaml'
    if profile_path.exists():
        with open(profile_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}

def analyse_job(job_data: Dict) -> Dict:
    """
    Phân tích job theo 7-tier CEO MODE:
    1. Intent Analysis
    2. Tech Feasibility
    3. Scope Creep Detection
    4. ROI Check Real
    5. Competition Intel
    6. Tier Matching
    7. Verdict
    """
    profile = load_profile()
    
    # Build prompt với tư duy logic và phân tích sâu
    prompt = f"""Bạn là Lysa - AI phân tích job chuyên nghiệp, có tư duy logic và phân tích sâu. Bạn hỗ trợ Tuấn Anh (freelancer).

TƯ DUY PHÂN TÍCH:
- Suy nghĩ đa chiều: xem xét job từ nhiều góc độ (client, market, competition, skills match)
- Logic rõ ràng: mỗi nhận định đều có lý do cụ thể, không nói chung chung
- Phân tích sâu: không chỉ nhìn bề ngoài, mà đi sâu vào intent, risk, opportunity
- Thực tế: dựa trên data và experience, không đoán mò
- Cân nhắc trade-offs: không chỉ thấy lợi mà còn thấy hại, không chỉ thấy cơ hội mà còn thấy rủi ro

{analysis_rules}

{upwork_rules}

{hardware_rules}

{profile_context}

PROFILE FREELANCER (Tuấn Anh - freelancer thật):
{json.dumps(profile, ensure_ascii=False, indent=2)}

QUAN TRỌNG: Profile trên là của Tuấn Anh (freelancer thật), không phải "CEO Lysa". Bạn phải phân tích jobs dựa trên skills/tech stack thực tế của Tuấn Anh.

JOB CẦN PHÂN TÍCH:
Title: {job_data.get('title', 'N/A')}
Description: {job_data.get('description', 'N/A')[:800]}
Budget: {job_data.get('budget', 'N/A')}
Source: {job_data.get('source', 'N/A')}
Link: {job_data.get('link', 'N/A')}

Hãy phân tích job này theo đúng 7 tầng CEO MODE:
1. INTENT ANALYSIS
2. TECH FEASIBILITY
3. SCOPE CREEP DETECTION
4. ROI CHECK REAL
5. COMPETITION INTEL
6. TIER MATCHING
7. VERDICT

VÍ DỤ PHÂN TÍCH (Few-shot learning):

Example 1 - Job phù hợp:
Job: "Python Web Scraper - Extract data from e-commerce sites"
{{
  "intent_analysis": "Client cần scrape data từ e-commerce, extract product info, prices. Rõ ràng, không mơ hồ.",
  "tech_feasibility": "HIGH - Match 100% với skills: Python, Requests/BeautifulSoup, data extraction",
  "scope_creep_detection": "Ít risk - chỉ scrape, không có yêu cầu thêm ML/AI phức tạp",
  "roi_check_real": "Budget $500-1000, thời gian 1-2 tuần. ROI tốt cho Tuấn Anh (rate 15$/h)",
  "competition_intel": "Có thể có nhiều proposals, nhưng demo-first approach sẽ nổi bật",
  "tier_matching": "Tier 2-3 - Mid-level, phù hợp với 8 năm exp của Tuấn Anh",
  "verdict": "NÊN LẤY",
  "score": 85,
  "keywords": ["Python", "Web Scraping", "Data Extraction"],
  "category": "Web Scraping"
}}

Example 2 - Job không phù hợp:
Job: "Senior React Developer - Build complex SPA with Redux"
{{
  "intent_analysis": "Client cần React/Redux developer, frontend focus",
  "tech_feasibility": "LOW - Tuấn Anh không có React trong tech stack, chủ yếu Python backend/scraping",
  "scope_creep_detection": "Medium risk - có thể yêu cầu thêm TypeScript, testing",
  "roi_check_real": "Budget cao nhưng không match skills",
  "competition_intel": "Nhiều React devs sẽ apply, Tuấn Anh không có lợi thế",
  "tier_matching": "Tier 1 - Senior level nhưng không match tech stack",
  "verdict": "KHÔNG NÊN LẤY",
  "score": 25,
  "keywords": ["React", "Frontend", "Redux"],
  "category": "Frontend"
}}

QUAN TRỌNG: BẮT BUỘC trả về CHỈ JSON, không có text, không có markdown, không có giải thích. Bắt đầu bằng {{ và kết thúc bằng }}.

Trả lời CHỈ JSON (copy-paste format này và fill vào):
{{
  "intent_analysis": "...",
  "tech_feasibility": "HIGH/MEDIUM/LOW - [lý do cụ thể]",
  "scope_creep_detection": "...",
  "roi_check_real": "...",
  "competition_intel": "...",
  "tier_matching": "Tier 1-5 - [phân tích]",
  "verdict": "NÊN LẤY / KHÔNG NÊN LẤY",
  "score": 0-100,
  "keywords": ["keyword1", "keyword2"],
  "category": "category_name"
}}
"""

    try:
        # Sử dụng Client với timeout để tránh hang
        from ollama import Client
        client = Client(host=ollama_base_url, timeout=90.0)  # 90s timeout
        
        response = client.chat(
            model=ollama_model,
            messages=[
                {
                    'role': 'system',
                    'content': 'Bạn là Lysa - AI phân tích job chuyên nghiệp, có tư duy logic, phân tích sâu, thực tế, không vòng vo. Bạn suy nghĩ đa chiều và đưa ra nhận định có lý do rõ ràng.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            options={
                'temperature': 0.5,  # Tăng lên 0.5 để có tư duy linh hoạt hơn nhưng vẫn logic
                'num_predict': 2000,
                'top_p': 0.85,  # Cho phép đa dạng trong phân tích
            }
        )
        
        result_text = response['message']['content']
        
        # Try to extract JSON from response - improved extraction
        try:
            import re
            # Method 1: Try to find JSON in code block first
            json_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', result_text, re.DOTALL)
            if json_block_match:
                analysis = json.loads(json_block_match.group(1))
            else:
                # Method 2: Find first complete JSON object by counting braces
                start_idx = result_text.find('{')
                if start_idx != -1:
                    brace_count = 0
                    end_idx = start_idx
                    for i in range(start_idx, len(result_text)):
                        if result_text[i] == '{':
                            brace_count += 1
                        elif result_text[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end_idx = i
                                break
                    if brace_count == 0:
                        json_str = result_text[start_idx:end_idx+1]
                        analysis = json.loads(json_str)
                    else:
                        # Method 3: Fallback to regex (non-greedy)
                        json_match = re.search(r'\{.*?\}', result_text, re.DOTALL)
                        if json_match:
                            analysis = json.loads(json_match.group())
                        else:
                            raise ValueError("No JSON found in response")
                else:
                    raise ValueError("No JSON found in response")
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse JSON from AI response for job {job_data.get('job_id', 'unknown')}: {e}")
            # Try to extract at least score and verdict from text
            score_match = re.search(r'"score":\s*(\d+)', result_text)
            verdict_match = re.search(r'"verdict":\s*"([^"]+)"', result_text)
            analysis = {
                'raw_response': result_text[:500],  # Limit raw response length
                'score': int(score_match.group(1)) if score_match else 50,
                'verdict': verdict_match.group(1) if verdict_match else 'CẦN XEM XÉT'
            }
        except Exception as e:
            logger.error(f"Error parsing AI response for job {job_data.get('job_id', 'unknown')}: {e}", exc_info=True)
            analysis = {
                'raw_response': result_text[:500],
                'score': 50,
                'verdict': 'CẦN XEM XÉT'
            }
        
        # Add metadata
        analysis['job_id'] = job_data.get('job_id')
        analysis['analysed_at'] = __import__('datetime').datetime.utcnow().isoformat()
        
        logger.info(f"Successfully analyzed job {job_data.get('job_id', 'unknown')}: {analysis.get('verdict', 'N/A')}")
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing job {job_data.get('job_id', 'unknown')}: {e}", exc_info=True)
        return {
            'error': str(e),
            'job_id': job_data.get('job_id'),
            'score': 0,
            'verdict': 'LỖI PHÂN TÍCH'
        }

def detect_category(job_data: Dict, keywords: List[str]) -> str:
    """Detect category từ keywords"""
    title_lower = (job_data.get('title', '') or '').lower()
    desc_lower = (job_data.get('description', '') or '').lower()
    
    text = f"{title_lower} {desc_lower}"
    
    for keyword in keywords:
        if keyword.lower() in text:
            return keyword
    
    return "General"

def extract_trends(job_data: Dict) -> List[str]:
    """Extract trending keywords từ job"""
    text = f"{job_data.get('title', '')} {job_data.get('description', '')}"
    text_lower = text.lower()
    
    # Common tech keywords
    tech_keywords = [
        'python', 'javascript', 'react', 'node.js', 'laravel', 'wordpress',
        'api', 'automation', 'scraping', 'ai', 'ml', 'data processing',
        'e-commerce', 'shopify', 'full stack', 'frontend', 'backend'
    ]
    
    found_keywords = []
    for keyword in tech_keywords:
        if keyword in text_lower:
            found_keywords.append(keyword)
    
    return found_keywords[:5]  # Top 5

def score_job(job_data: Dict, analysis: Dict) -> int:
    """Score job từ 0-100 dựa trên analysis"""
    score = 50  # Base score
    
    # Verdict impact
    verdict = analysis.get('verdict', '').upper()
    if 'NÊN LẤY' in verdict:
        score += 30
    elif 'KHÔNG NÊN' in verdict:
        score -= 30
    
    # Budget impact
    budget = job_data.get('budget')
    if budget:
        try:
            budget_num = float(str(budget).replace('$', '').replace(',', ''))
            if budget_num > 1000:
                score += 10
            elif budget_num < 100:
                score -= 10
        except:
            pass
    
    # Scope creep penalty
    scope_text = analysis.get('scope_creep_detection', '').lower()
    if 'scope creep' in scope_text or 'phình scope' in scope_text:
        score -= 20
    
    # ROI positive
    roi_text = analysis.get('roi_check_real', '').lower()
    if 'lời' in roi_text or 'tốt' in roi_text:
        score += 10
    
    return max(0, min(100, score))

if __name__ == '__main__':
    # Test
    test_job = {
        'job_id': 'test123',
        'title': 'Python Web Scraping Project',
        'description': 'Need Python developer to scrape data from websites. Budget $500.',
        'budget': '$500',
        'source': 'RemoteOK',
        'link': 'https://example.com'
    }
    
    result = analyse_job(test_job)
    print(json.dumps(result, ensure_ascii=False, indent=2))

