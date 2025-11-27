#!/usr/bin/env python3
"""
Data Validation Utility - Validate job data before saving
"""

from typing import Dict, List, Optional, Tuple

def validate_job(job_data: Dict) -> Tuple[bool, List[str]]:
    """
    Validate job data structure and required fields
    
    Args:
        job_data: Job dictionary to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Required fields (source có thể default nếu thiếu)
    required_fields = ['job_id', 'title', 'link']
    for field in required_fields:
        if not job_data.get(field):
            errors.append(f"Missing required field: {field}")
    
    # Source có thể default nếu thiếu
    if not job_data.get('source'):
        # Không thêm vào errors, sẽ được set default sau
        pass
    
    # Validate job_id
    job_id = job_data.get('job_id', '')
    if job_id:
        if not isinstance(job_id, str):
            errors.append("job_id must be a string")
        elif len(job_id.strip()) == 0:
            errors.append("job_id cannot be empty")
    
    # Validate title
    title = job_data.get('title', '')
    if title:
        if not isinstance(title, str):
            errors.append("title must be a string")
        elif len(title.strip()) == 0:
            errors.append("title cannot be empty")
        elif len(title) > 500:
            errors.append(f"title too long ({len(title)} chars, max 500)")
    
    # Validate description (sẽ được sanitize tự động nếu quá dài)
    description = job_data.get('description', '')
    if description:
        if not isinstance(description, str):
            errors.append("description must be a string")
        # Note: Description quá dài sẽ được sanitize tự động, không reject
    
    # Validate link
    link = job_data.get('link', '')
    if link:
        if not isinstance(link, str):
            errors.append("link must be a string")
        elif not link.startswith(('http://', 'https://')):
            errors.append("link must be a valid URL")
    
    # Validate source
    source = job_data.get('source', '')
    if source:
        if not isinstance(source, str):
            errors.append("source must be a string")
        elif len(source.strip()) == 0:
            errors.append("source cannot be empty")
    
    # Validate budget (optional but should be string or number if present)
    budget = job_data.get('budget')
    if budget is not None:
        if not isinstance(budget, (str, int, float)):
            errors.append("budget must be string, int, or float")
    
    # Validate proposals (optional but should be int if present)
    proposals = job_data.get('proposals')
    if proposals is not None:
        if not isinstance(proposals, (str, int)):
            errors.append("proposals must be string or int")
    
    is_valid = len(errors) == 0
    return is_valid, errors

def sanitize_job(job_data: Dict) -> Dict:
    """
    Sanitize job data (trim strings, normalize types, set defaults)
    
    Args:
        job_data: Job dictionary to sanitize
        
    Returns:
        Sanitized job dictionary
    """
    sanitized = job_data.copy()
    
    # Set default source nếu thiếu
    if not sanitized.get('source'):
        sanitized['source'] = 'Unknown'
    
    # Trim string fields
    string_fields = ['job_id', 'title', 'description', 'link', 'source', 'category', 'client_country']
    for field in string_fields:
        if field in sanitized and isinstance(sanitized[field], str):
            sanitized[field] = sanitized[field].strip()
    
    # Limit description length (tự động truncate thay vì reject)
    if 'description' in sanitized:
        desc = sanitized.get('description', '')
        if isinstance(desc, str) and len(desc) > 10000:
            sanitized['description'] = desc[:10000] + '...'
    
    # Limit title length
    if 'title' in sanitized:
        title = sanitized.get('title', '')
        if isinstance(title, str) and len(title) > 500:
            sanitized['title'] = title[:500]
    
    return sanitized

