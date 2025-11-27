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
    
    # Build prompt ngắn gọn hơn để nhanh hơn
    profile_summary = f"Tuấn Anh: {profile.get('title', 'Python Developer')}, {profile.get('experience', 0)} năm exp, skills: {', '.join(profile.get('skills', [])[:5])}"
    
    # Rút ngắn description để prompt nhanh hơn
    desc = job_data.get('description', 'N/A')
    if len(desc) > 400:
        desc = desc[:400] + "..."
    
    prompt = f"""Phân tích job cho Tuấn Anh (Python/Scraping/Automation).

Profile: {profile_summary}
Job: {job_data.get('title', 'N/A')}
Desc: {desc}
Budget: {job_data.get('budget', 'N/A')}

Phân tích ngắn gọn:
1. INTENT - Client muốn gì?
2. TECH - Match skills? (HIGH/MED/LOW)
3. SCOPE - Risk phình scope?
4. ROI - Lời bao nhiêu?
5. COMPETITION - Nhiều người apply?
6. TIER - Tier 1-5
7. VERDICT - NÊN LẤY / KHÔNG NÊN LẤY

Trả về CHỈ JSON:
{{
  "intent_analysis": "...",
  "tech_feasibility": "HIGH/MEDIUM/LOW",
  "scope_creep_detection": "...",
  "roi_check_real": "...",
  "competition_intel": "...",
  "tier_matching": "Tier X",
  "verdict": "NÊN LẤY / KHÔNG NÊN LẤY",
  "score": 0-100,
  "keywords": ["kw1"],
  "category": "category"
}}"""

    try:
        # Tăng timeout lên 60s và thêm retry logic
        from ollama import Client
        import time
        
        client = Client(host=ollama_base_url, timeout=60.0)  # Tăng lên 60s
        
        # Retry logic với exponential backoff
        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = client.chat(
                    model=ollama_model,
                    messages=[
                        {
                            'role': 'system',
                            'content': 'Bạn là Lysa. Trả về CHỈ JSON, không text khác.'
                        },
                        {
                            'role': 'user',
                            'content': prompt
                        }
                    ],
                    options={
                        'temperature': 0.2,  # Giảm xuống 0.2 để nhanh và chính xác hơn
                        'num_predict': 600,  # Giảm xuống 600 để nhanh hơn
                        'top_p': 0.7,
                        'top_k': 30,
                    }
                )
                break  # Thành công, thoát retry loop
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # 2s, 4s
                    logger.warning(f"Retry {attempt + 1}/{max_retries} after {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    raise  # Nếu hết retry thì raise exception
        
        result_text = response['message']['content']
        
        # Log raw response để debug (chỉ log 200 ký tự đầu)
        logger.debug(f"Raw AI response (first 200 chars): {result_text[:200]}")
        
        # Try to extract JSON from response - improved extraction với nhiều methods
        analysis = None
        import re
        
        try:
            # Method 1: Try to find JSON in code block first
            json_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', result_text, re.DOTALL)
            if json_block_match:
                try:
                    analysis = json.loads(json_block_match.group(1))
                    logger.debug("Parsed JSON from code block")
                except json.JSONDecodeError:
                    pass
            
            # Method 2: Find first complete JSON object by counting braces
            if not analysis:
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
                        try:
                            analysis = json.loads(json_str)
                            logger.debug("Parsed JSON by brace counting")
                        except json.JSONDecodeError:
                            pass
            
            # Method 3: Try to find JSON-like structure (có thể có lỗi nhỏ)
            if not analysis:
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', result_text, re.DOTALL)
                if json_match:
                    try:
                        # Try to fix common JSON errors
                        json_str = json_match.group()
                        # Fix unquoted keys
                        json_str = re.sub(r'(\w+):', r'"\1":', json_str)
                        # Fix single quotes
                        json_str = json_str.replace("'", '"')
                        analysis = json.loads(json_str)
                        logger.debug("Parsed JSON with fixes")
                    except (json.JSONDecodeError, Exception):
                        pass
            
            # Method 4: Try to extract fields from text và build JSON manually
            if not analysis:
                logger.warning(f"No JSON found in response for job {job_data.get('job_id', 'unknown')}. Response: {result_text[:300]}")
                # Extract fields từ text
                score_match = re.search(r'(?:score|điểm)[:\s]+(\d+)', result_text, re.IGNORECASE)
                verdict_match = re.search(r'(?:verdict|kết luận|quyết định)[:\s]+(NÊN LẤY|KHÔNG NÊN LẤY|CẦN XEM XÉT)', result_text, re.IGNORECASE)
                tech_match = re.search(r'(?:tech|kỹ thuật)[:\s]+(HIGH|MEDIUM|LOW|CAO|TRUNG BÌNH|THẤP)', result_text, re.IGNORECASE)
                
                analysis = {
                    'intent_analysis': result_text[:200] if len(result_text) > 50 else result_text,
                    'tech_feasibility': tech_match.group(1) if tech_match else 'MEDIUM',
                    'scope_creep_detection': 'Cần xem xét',
                    'roi_check_real': 'Cần xem xét',
                    'competition_intel': 'Cần xem xét',
                    'tier_matching': 'Tier 3',
                    'verdict': verdict_match.group(1) if verdict_match else 'CẦN XEM XÉT',
                    'score': int(score_match.group(1)) if score_match else 50,
                    'keywords': [],
                    'category': 'General',
                    'raw_response': result_text[:500],
                    'parse_method': 'text_extraction'
                }
            
            # Ensure analysis is not None
            if not analysis:
                analysis = {
                    'raw_response': result_text[:500],
                    'score': 50,
                    'verdict': 'CẦN XEM XÉT'
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

