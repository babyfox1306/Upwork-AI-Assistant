# Upwork AI Assistant - Feed Aggregator Edition

**Lysa** - AI Assistant phân tích job market từ nhiều nguồn an toàn, hợp pháp.

## 🎯 Đặc điểm

- ✅ **100% An toàn**: Không đụng vào Upwork, không vi phạm ToS
- ✅ **Nhiều nguồn**: 20+ job boards, tech blogs, RSS feeds hợp pháp
- ✅ **AI thông minh**: Phân tích job theo CEO MODE 7-tier, học trend tự động
- ✅ **Tự động hóa**: GitHub Actions crawl mỗi 15 phút
- ✅ **Local AI**: Chạy trên Ollama local, không cần API key

## 📋 Yêu cầu

- Python 3.10
- Ollama với model `qwen2.5:7b-instruct-q4_K_M`
- Git

## 🚀 Setup

### 1. Clone repository

```bash
git clone https://github.com/babyfox1306/Upwork-AI-Assistant.git
cd Upwork-AI-Assistant
```

### 2. Setup Python environment

```bash
# Windows
setup.bat

# Linux/Mac
python -m venv venv
source venv/bin/activate  # hoặc venv\Scripts\activate trên Windows
pip install -r requirements.txt
```

### 3. Setup Ollama

```bash
# Cài Ollama nếu chưa có
# https://ollama.ai

# Pull model
ollama pull qwen2.5:7b-instruct-q4_K_M
ollama pull all-minilm
```

### 4. Cấu hình

Chỉnh sửa `config/profile.yaml` với thông tin của bạn:
- Skills
- Experience
- Rate
- Portfolio

## 📖 Sử dụng

### Cập nhật dữ liệu

```bash
# Windows
update.bat

# Hoặc manual
python scripts/crawl_multi_source.py
python scripts/local_sync_and_rag.py
python scripts/analyze_and_summarize.py
```

### Chat với AI

```bash
# Windows
chat.bat

# Hoặc manual
streamlit run app.py
```

Mở trình duyệt tại `http://localhost:8501`

### Phân tích job cụ thể

```python
from ai.analyser import analyse_job

job = {
    'title': 'Python Web Scraping',
    'description': '...',
    'budget': '$500'
}

result = analyse_job(job)
print(result)
```

### Generate proposal

```python
from ai.generator import generate_proposal

proposal = generate_proposal(job_id='abc123')
# hoặc
proposal = generate_proposal(job_link='https://...')
```

### Xem daily summary

```python
from ai.summarizer import generate_daily_summary

summary = generate_daily_summary()
print(summary['summary'])
```

## 📁 Cấu trúc

```
Upwork-AI-Assistant/
├── ai/                      # AI modules
│   ├── analyser.py         # Phân tích job (7-tier CEO MODE)
│   ├── summarizer.py       # Tóm tắt trend hàng ngày/tuần
│   └── generator.py        # Generate proposal draft
├── ai_rules/               # AI instructions
│   ├── analysis.md         # System instruction
│   ├── upwork_rules.md     # Rulebook
│   ├── examples.json       # Few-shot examples
│   └── hardware.md         # Hardware constraints
├── config/
│   ├── config.yaml         # RSS feeds, Ollama config
│   ├── profile.yaml        # CEO profile
│   └── proposal_template.txt
├── data/
│   ├── raw_jobs.jsonl      # Jobs từ RSS (git tracked)
│   ├── feeds/              # Tech blog feeds (gitignore)
│   ├── trends/             # Daily/weekly summaries
│   ├── analyses/           # AI analyses
│   └── chroma_db/          # Vector DB (gitignore)
├── scripts/
│   ├── crawl_multi_source.py    # Crawl RSS feeds
│   ├── local_sync_and_rag.py     # Sync + embed + ChromaDB
│   ├── analyze_and_summarize.py  # AI analysis + summary
│   ├── query_ai.py               # Query AI
│   └── generator.py              # Generate proposal
├── .github/workflows/
│   └── crawl.yml           # GitHub Actions (crawl mỗi 15 phút)
├── app.py                   # Streamlit chat interface
├── update.bat               # Update script (Windows)
└── chat.bat                 # Chat script (Windows)
```

## 🔧 Cấu hình RSS Feeds

Chỉnh sửa `config/config.yaml` để thêm/bật/tắt RSS feeds:

```yaml
sources:
  job_boards:
    - name: "We Work Remotely"
      url: "https://..."
      enabled: true
      category: "jobs"
  
  tech_blogs:
    - name: "OpenAI Blog"
      url: "https://openai.com/blog/rss.xml"
      enabled: true
      category: "trends"
  
  google_alerts:
    - name: "AI Freelance Remote"
      url: ""  # Paste RSS URL từ Google Alerts
      enabled: false
```

### Setup Google Alerts RSS

1. Vào https://www.google.com/alerts
2. Tạo alert với từ khóa (ví dụ: "AI freelance remote")
3. Chọn "Deliver to: RSS feed"
4. Copy RSS URL vào `config/config.yaml`

## 🤖 AI Analysis - CEO MODE 7-Tier

Lysa phân tích mỗi job theo 7 tầng:

1. **INTENT ANALYSIS** - Lý do khách post job
2. **TECH FEASIBILITY** - Có gì không thực tế?
3. **SCOPE CREEP DETECTION** - Mùi phình scope
4. **ROI CHECK REAL** - Lời bao nhiêu theo giờ?
5. **COMPETITION INTEL** - Số proposal, cheap labor trap
6. **TIER MATCHING** - Job này hợp với mình không?
7. **VERDICT** - CHỐT: Nên lấy / Không nên

## 🔄 GitHub Actions

Workflow tự động:
- Crawl RSS feeds mỗi 15 phút
- Commit jobs mới vào repo
- Pull về local để AI phân tích

## 📊 Data Flow

```
GitHub Actions (15 phút/lần)
    ↓
Crawl RSS Feeds (job boards, tech blogs)
    ↓
Commit vào data/raw_jobs.jsonl
    ↓
Local: git pull
    ↓
AI Analysis (analyser.py)
    ↓
Daily/Weekly Summary (summarizer.py)
    ↓
ChromaDB (vector search)
    ↓
Streamlit Chat Interface
```

## 🛡️ An toàn

- ✅ Không crawl Upwork
- ✅ Chỉ dùng RSS feeds công khai
- ✅ Không vi phạm ToS
- ✅ Không cần API keys (trừ Ollama local)
- ✅ Tất cả nguồn đều hợp pháp

## 📝 License

MIT

## 🤝 Contributing

Pull requests welcome!

---

**Lysa** - Your AI Job Market Analyst 🤖

