# Upwork AI Assistant - Feed Aggregator Edition

**Lysa** - AI Assistant phân tích job market từ nhiều nguồn an toàn, hợp pháp.

## 🎯 Đặc điểm

- ✅ **100% An toàn**: Không đụng vào Upwork, không vi phạm ToS
- ✅ **Nhiều nguồn**: 5+ job boards nhanh, 10+ tech blogs, RSS feeds hợp pháp
- ✅ **AI thông minh**: Phân tích job theo CEO MODE 7-tier, học trend tự động
- ✅ **Tự động hóa**: GitHub Actions crawl mỗi 15 phút
- ✅ **Local AI**: Chạy trên Ollama local, không cần API key
- ✅ **Tối ưu**: Loại bỏ duplicate, skip jobs không hợp lệ, nhanh hơn 50%

## 📋 Yêu cầu

- Python 3.10+
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
# Windows (khuyến nghị)
setup.bat

# Linux/Mac
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Setup Ollama

```bash
# Cài Ollama nếu chưa có
# https://ollama.ai

# Pull model
ollama pull qwen2.5:7b-instruct-q4_K_M
```

### 4. Cấu hình

Chỉnh sửa `config/profile.yaml` với thông tin của bạn:
- Skills
- Experience
- Rate
- Portfolio

## 📖 Sử dụng

### Cập nhật dữ liệu

**Windows (khuyến nghị):**
```bash
update.bat
```

Chọn chế độ:
- **1. Đầy đủ** (mặc định): Git Pull + Sync ChromaDB + AI Analysis
- **2. Chỉ Sync**: Chỉ sync ChromaDB (nhanh, không AI analysis)

**Manual:**
```bash
# Pull data từ GitHub
git pull origin main

# Sync ChromaDB
python scripts/local_sync_and_rag.py

# AI Analysis (tùy chọn)
python scripts/analyze_and_summarize.py
```

### Chat với AI

**Windows:**
```bash
chat.bat
```

**Manual:**
```bash
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

## 📁 Cấu trúc

```
Upwork-AI-Assistant/
├── ai/                      # AI modules
│   ├── analyser.py         # Phân tích job (7-tier CEO MODE)
│   ├── summarizer.py       # Tóm tắt trend hàng ngày/tuần
│   └── generator.py        # Generate proposal draft
├── ai_rules/               # AI instructions
│   ├── analysis.md         # System instruction
│   ├── upwork_rules.md     # Rulebook (7-tier analysis)
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
│   └── write_proposal.py         # Generate proposal
├── .github/workflows/
│   └── crawl.yml           # GitHub Actions (crawl mỗi 15 phút)
├── app.py                   # Streamlit chat interface
├── setup.bat                # Setup script (Windows)
├── update.bat               # Update script (Windows) - 2 chế độ
└── chat.bat                 # Chat script (Windows)
```

## 🔧 Cấu hình RSS Feeds

Chỉnh sửa `config/config.yaml` để thêm/bật/tắt RSS feeds:

```yaml
sources:
  job_boards:
    - name: "We Work Remotely - Programming"
      url: "https://weworkremotely.com/categories/remote-programming-jobs.rss"
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

**Tone**: Thẳng, thực dụng, quyết đoán, không vòng vo.

## 🔄 GitHub Actions

Workflow tự động:
- Crawl RSS feeds mỗi 15 phút
- Chỉ crawl job boards (skip tech blogs trong CI để nhanh)
- Commit jobs mới vào repo
- Pull về local để AI phân tích

## 📊 Data Flow

```
GitHub Actions (15 phút/lần)
    ↓
Crawl RSS Feeds (job boards)
    ↓
Commit vào data/raw_jobs.jsonl
    ↓
Local: update.bat
    ↓
Git Pull
    ↓
Sync ChromaDB (embedding, loại duplicate)
    ↓
AI Analysis (top 5 jobs mới)
    ↓
Daily Summary (nếu có jobs mới)
    ↓
Streamlit Chat Interface
```

## ⚡ Tối ưu Performance

- **Duplicate Detection**: Tự động loại bỏ jobs trùng lặp
- **Smart Filtering**: Skip jobs không hợp lệ (thiếu ID, JSON lỗi)
- **Batch Processing**: Embedding theo batch để nhanh hơn
- **Selective Analysis**: Chỉ phân tích top 5 jobs mới (giảm từ 10)
- **Skip Summary**: Bỏ qua daily summary nếu không có jobs mới

## 🛡️ An toàn

- ✅ Không crawl Upwork
- ✅ Chỉ dùng RSS feeds công khai
- ✅ Không vi phạm ToS
- ✅ Không cần API keys (trừ Ollama local)
- ✅ Tất cả nguồn đều hợp pháp

## 🐛 Troubleshooting

### Lỗi encoding trong batch files
- Đã fix: Tất cả batch files dùng `chcp 65001` và tiếng Việt không dấu

### Lỗi duplicate IDs khi sync
- Đã fix: Tự động loại bỏ duplicate trong batch trước khi add vào ChromaDB

### Sync lâu
- Dùng chế độ 2 trong `update.bat` (chỉ sync, không AI analysis)
- Hoặc chờ AI analysis hoàn thành (1-2 phút cho 5 jobs)

### Không có jobs mới
- Bình thường: Crawler chỉ lấy jobs MỚI (không duplicate)
- Đợi jobs mới xuất hiện trên feeds hoặc kiểm tra GitHub Actions logs

## 📝 License

MIT

## 🤝 Contributing

Pull requests welcome!

---

**Lysa** - Your AI Job Market Analyst 🤖
