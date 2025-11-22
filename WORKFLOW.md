# Workflow - Cách hệ thống hoạt động

## 🔄 Tự động (GitHub Actions)

**GitHub Actions chạy tự động mỗi 15 phút:**

1. Crawl RSS feeds từ job boards (5 feeds nhanh)
2. Skip tech blogs trong CI để tiết kiệm thời gian
3. Lưu jobs mới vào `data/raw_jobs.jsonl`
4. Commit và push lên GitHub repo

→ **Bạn không cần làm gì**, GitHub tự động làm việc này.

## 👤 Việc của bạn (Local)

**Chạy `update.bat` khi muốn cập nhật:**

```bash
.\update.bat
```

### Chế độ 1: Đầy đủ (mặc định)

1. **Pull data mới** từ GitHub (jobs mà GitHub Actions đã crawl)
2. **Sync ChromaDB** - Embedding jobs mới vào vector database
   - Tự động loại bỏ duplicate
   - Skip jobs không hợp lệ
3. **AI Analysis** - Phân tích top 5 jobs mới và generate summary
   - Chỉ phân tích nếu có jobs mới
   - Skip summary nếu không có jobs mới

**Thời gian**: ~1-2 phút (tùy số jobs mới)

### Chế độ 2: Chỉ Sync (nhanh)

1. **Sync ChromaDB** - Chỉ embedding jobs mới
   - Không git pull
   - Không AI analysis

**Thời gian**: ~30 giây

→ **Chạy khi nào?** 
- **Chế độ 1**: Mỗi ngày 1 lần (để có data mới + AI analysis)
- **Chế độ 2**: Khi muốn sync nhanh, không cần AI analysis

## 📊 Data Flow

```
GitHub Actions (mỗi 15 phút)
    ↓
Crawl RSS Feeds (job boards)
    ↓
Lưu vào data/raw_jobs.jsonl
    ↓
Commit & Push lên GitHub
    ↓
[Local] Bạn chạy update.bat
    ↓
Chế độ 1: Pull data từ GitHub
    ↓
Sync ChromaDB (embedding, loại duplicate)
    ↓
AI Analysis (top 5 jobs mới)
    ↓
Daily Summary (nếu có jobs mới)
    ↓
Sẵn sàng để chat với Lysa!
```

## 🛠️ Scripts

### `update.bat`
- **Chế độ 1**: Pull + Sync + AI Analysis (đầy đủ)
- **Chế độ 2**: Chỉ Sync (nhanh)
- Chạy khi muốn cập nhật data

### `chat.bat`
- Mở Streamlit interface để chat với Lysa
- Phân tích jobs, generate proposal, xem trends
- Chạy khi muốn hỏi AI

### `setup.bat`
- Setup lần đầu: tạo venv, cài dependencies, pull Ollama model
- Chỉ chạy 1 lần khi mới clone repo

## ⚡ Tối ưu

- **Duplicate Detection**: Tự động loại bỏ jobs trùng lặp
- **Smart Filtering**: Skip jobs không hợp lệ
- **Selective Analysis**: Chỉ phân tích top 5 jobs mới
- **Skip Summary**: Bỏ qua nếu không có jobs mới
- **CI Optimization**: Skip tech blogs trong GitHub Actions

## ⚡ Tóm tắt

- **GitHub Actions**: Tự động crawl mỗi 15 phút → bạn không cần làm gì
- **update.bat (chế độ 1)**: Pull + sync + AI analysis → chạy mỗi ngày
- **update.bat (chế độ 2)**: Chỉ sync → chạy khi muốn nhanh
- **chat.bat**: Chat với Lysa → chạy khi muốn hỏi AI

---

**Lưu ý**: Không cần crawl thủ công nữa vì GitHub Actions đã làm rồi. Chỉ cần `update.bat` để pull và xử lý data mới.
