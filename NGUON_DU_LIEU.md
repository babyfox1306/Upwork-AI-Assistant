# Nguồn Dữ Liệu Jobs - Multi-Source Support

## 🎯 Quan Điểm

Hệ thống **KHÔNG giới hạn** chỉ lấy dữ liệu từ Upwork. AI có thể phân tích và hiểu jobs từ **bất kỳ nguồn uy tín nào**.

## ✅ Các Nguồn Đang Hỗ Trợ

### 1. RSS Feeds (Đang hoạt động)

- ✅ **We Work Remotely**: https://weworkremotely.com/categories/remote-programming-jobs.rss
  - Status: Hoạt động tốt
  - Jobs: ~25 jobs mỗi lần crawl
  
- ⚠️ **Indeed RSS**: Cần authentication hoặc bị chặn
- ⚠️ **RemoteOK RSS**: Redirect 301
- ⚠️ **Stack Overflow Jobs RSS**: Cần authentication

### 2. APIs (Có thể mở rộng)

- ⚠️ **GitHub Jobs API**: Đã ngừng hoạt động (2021)
- Có thể thêm:
  - **Remote.co API**
  - **AngelList API**
  - **LinkedIn Jobs API** (cần auth)

### 3. Web Scraping (Tùy chọn)

- **Freelancer.com**: Có thể scrape (cần cẩn thận với ToS)
- **Guru.com**: Có thể scrape
- **Toptal**: Có thể scrape

## 🔧 Cách Thêm Nguồn Mới

### Thêm RSS Feed

Chỉnh sửa `config/config.yaml`:

```yaml
sources:
  rss_feeds:
    - name: "Tên Nguồn"
      url: "https://example.com/jobs.rss"
      enabled: true
      type: "rss"
```

### Thêm API Source

```yaml
sources:
  api_sources:
    - name: "Tên API"
      url: "https://api.example.com/jobs"
      enabled: true
      type: "api"
      params:
        key: "value"
```

## 📊 Normalization

Tất cả jobs từ các nguồn khác nhau được **normalize** về cùng format:

```json
{
  "job_id": "unique_id",
  "title": "Job Title",
  "description": "Job description...",
  "link": "https://...",
  "budget": "1200",
  "proposals": "8",
  "client_country": "USA",
  "category": "WordPress",
  "source": "We Work Remotely",
  "source_type": "rss",
  "created_at": "2025-01-20T10:00:00",
  "crawled_at": "2025-01-20T10:05:00"
}
```

## 🤖 AI Phân Tích

AI **không quan tâm** nguồn gốc của job. Chỉ cần:
- Title và description rõ ràng
- Format chuẩn
- Đủ thông tin để phân tích

AI sẽ tự động:
- Phát hiện scam
- Ước lượng tỉ lệ thắng
- Tìm điểm match với profile
- Đề xuất cách cá nhân hóa proposal

## 🚀 Chạy Crawl

```bash
# Crawl từ tất cả nguồn đã enable
python scripts/crawl_multi_source.py

# Sync và update ChromaDB
python scripts/local_sync_and_rag.py

# Query AI phân tích
python scripts/query_ai.py
```

## 💡 Gợi Ý Nguồn Uy Tín

### RSS Feeds
- We Work Remotely ✅
- Remote.co
- FlexJobs
- Working Nomads
- Remote Work Hub

### Job Boards
- Freelancer.com
- Guru.com
- PeoplePerHour
- 99designs
- Toptal

### Aggregators
- Indeed
- Glassdoor
- LinkedIn Jobs
- ZipRecruiter

## ⚠️ Lưu Ý

- **Tuân thủ ToS**: Đảm bảo nguồn cho phép crawl
- **Rate Limiting**: Không spam requests
- **Respect robots.txt**: Kiểm tra trước khi scrape
- **Privacy**: Không lưu thông tin nhạy cảm

## 🔄 Auto-Update

GitHub Actions sẽ tự động crawl mỗi 15 phút từ tất cả nguồn đã enable.

