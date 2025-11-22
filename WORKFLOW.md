# Workflow - Cách hệ thống hoạt động

## 🔄 Tự động (GitHub Actions)

**GitHub Actions chạy tự động mỗi 15 phút:**

1. Crawl RSS feeds từ job boards và tech blogs
2. Lưu jobs mới vào `data/raw_jobs.jsonl`
3. Commit và push lên GitHub repo

→ **Bạn không cần làm gì**, GitHub tự động làm việc này.

## 👤 Việc của bạn (Local)

**Chạy `update.bat` khi muốn cập nhật:**

```bash
.\update.bat
```

Script này sẽ:

1. **Pull data mới** từ GitHub (jobs mà GitHub Actions đã crawl)
2. **Sync ChromaDB** - Embedding jobs mới vào vector database
3. **AI Analysis** - Phân tích jobs mới và generate summary

→ **Chạy khi nào?** 
- Mỗi ngày 1 lần (để có data mới)
- Hoặc khi muốn xem jobs mới ngay

## 📊 Data Flow

```
GitHub Actions (mỗi 15 phút)
    ↓
Crawl RSS Feeds
    ↓
Lưu vào data/raw_jobs.jsonl
    ↓
Commit & Push lên GitHub
    ↓
[Local] Bạn chạy update.bat
    ↓
Pull data từ GitHub
    ↓
Sync ChromaDB (embedding)
    ↓
AI Analysis & Summary
    ↓
Sẵn sàng để chat với Lysa!
```

## 🛠️ Scripts khác

### `crawl_local.bat`
- Crawl thủ công ngay lập tức (không cần đợi GitHub Actions)
- Chỉ dùng khi muốn crawl ngay, không đợi 15 phút

### `chat.bat`
- Mở Streamlit interface để chat với Lysa
- Phân tích jobs, generate proposal, xem trends

## ⚡ Tóm tắt

- **GitHub Actions**: Tự động crawl mỗi 15 phút → bạn không cần làm gì
- **update.bat**: Pull data + sync + AI analysis → chạy khi muốn cập nhật
- **chat.bat**: Chat với Lysa → chạy khi muốn hỏi AI

---

**Lưu ý**: Không cần crawl thủ công nữa vì GitHub Actions đã làm rồi. Chỉ cần `update.bat` để pull và xử lý data mới.

