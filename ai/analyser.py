#!/usr/bin/env python3
"""
AI Job Analyser - Phân tích job, scoring, category detection, trend extraction
"""

import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional
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
analysis_rules = (ai_rules_path / 'analysis.md').read_text(encoding='utf-8')
upwork_rules = (ai_rules_path / 'upwork_rules.md').read_text(encoding='utf-8')
hardware_rules = (ai_rules_path / 'hardware.md').read_text(encoding='utf-8')

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
    
    # Build prompt
    prompt = f"""Bạn là Lysa - AI phân tích job chuyên nghiệp.

{analysis_rules}

{upwork_rules}

{hardware_rules}

PROFILE FREELANCER:
{json.dumps(profile, ensure_ascii=False, indent=2)}

JOB CẦN PHÂN TÍCH:
Title: {job_data.get('title', 'N/A')}
Description: {job_data.get('description', 'N/A')[:1000]}
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

Trả lời bằng JSON format:
{{
  "intent_analysis": "...",
  "tech_feasibility": "...",
  "scope_creep_detection": "...",
  "roi_check_real": "...",
  "competition_intel": "...",
  "tier_matching": "...",
  "verdict": "NÊN LẤY / KHÔNG NÊN LẤY",
  "score": 0-100,
  "keywords": ["keyword1", "keyword2"],
  "category": "category_name"
}}
"""

    try:
        response = ollama.chat(
            model=ollama_model,
            messages=[
                {
                    'role': 'system',
                    'content': 'Bạn là Lysa - AI phân tích job chuyên nghiệp, thực tế, không vòng vo.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        )
        
        result_text = response['message']['content']
        
        # Try to extract JSON from response
        try:
            # Tìm JSON trong response
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                # Fallback: parse manually
                analysis = {
                    'raw_response': result_text,
                    'score': 50,
                    'verdict': 'CẦN XEM XÉT'
                }
        except:
            analysis = {
                'raw_response': result_text,
                'score': 50,
                'verdict': 'CẦN XEM XÉT'
            }
        
        # Add metadata
        analysis['job_id'] = job_data.get('job_id')
        analysis['analysed_at'] = __import__('datetime').datetime.utcnow().isoformat()
        
        return analysis
        
    except Exception as e:
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

