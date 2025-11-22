#!/bin/bash
# Test script để simulate GitHub Actions environment
# Chạy trên Linux/Mac hoặc Git Bash trên Windows

echo "========================================"
echo "  Test Crawler (Simulate GitHub Actions)"
echo "========================================"
echo ""

# Set CI environment variables
export CI=true
export GITHUB_ACTIONS=true

echo "========================================"
echo "  Test: Crawl với CI mode"
echo "========================================"
echo ""

# Activate venv nếu có
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install dependencies
pip install --upgrade pip
pip install feedparser pyyaml requests beautifulsoup4

# Run crawler
python scripts/crawl_multi_source.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ TEST FAILED: Crawler có lỗi!"
    exit 1
fi

# Check output
if [ -f "data/raw_jobs.jsonl" ]; then
    echo ""
    echo "✓ File raw_jobs.jsonl tồn tại"
    echo "  Size: $(wc -c < data/raw_jobs.jsonl) bytes"
    echo "  Lines: $(wc -l < data/raw_jobs.jsonl) jobs"
else
    echo ""
    echo "❌ File raw_jobs.jsonl không tồn tại!"
    exit 1
fi

echo ""
echo "========================================"
echo "  ✅ TEST PASSED!"
echo "========================================"
echo ""
echo "Crawler hoạt động tốt, có thể push lên GitHub."
echo ""

