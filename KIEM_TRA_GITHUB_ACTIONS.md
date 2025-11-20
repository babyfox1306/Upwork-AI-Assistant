# Cách Kiểm Tra GitHub Actions Đang Chạy

## 1. Kiểm Tra Trên GitHub Web Interface

### Bước 1: Vào Tab Actions
1. Mở repo: https://github.com/babyfox1306/Upwork-AI-Assistant
2. Click tab **Actions** (ở trên cùng, bên cạnh Code, Issues...)

### Bước 2: Xem Workflow Runs
- Nếu workflow đã chạy, bạn sẽ thấy danh sách các runs
- Mỗi run sẽ hiển thị:
  - ✅ (màu xanh) = Thành công
  - ❌ (màu đỏ) = Thất bại
  - 🟡 (màu vàng) = Đang chạy
  - ⚪ (màu xám) = Chưa chạy

### Bước 3: Xem Chi Tiết
- Click vào một run để xem:
  - Logs từng bước
  - Thời gian chạy
  - Lỗi (nếu có)

## 2. Trigger Workflow Thủ Công (Test Ngay)

### Cách 1: Trên GitHub Web
1. Vào tab **Actions**
2. Chọn workflow **"Crawl Upwork RSS Jobs"** ở sidebar bên trái
3. Click **"Run workflow"** (nút ở bên phải)
4. Chọn branch **main**
5. Click **"Run workflow"** (nút xanh)

### Cách 2: Dùng GitHub CLI (nếu đã cài)
```bash
gh workflow run "Crawl Upwork RSS Jobs.yml"
```

## 3. Kiểm Tra Bằng Git

### Xem Commit History
```bash
git log --oneline --all --graph
```

Nếu thấy commit với message **"Auto-update: New jobs from RSS [skip ci]"** → GitHub Actions đã chạy và có jobs mới.

### Pull Data Mới
```bash
git pull
```

Nếu có file `data/raw_jobs.jsonl` được update → GitHub Actions đã crawl được jobs.

## 4. Kiểm Tra Settings

### Enable Actions (nếu chưa enable)
1. Vào repo → **Settings**
2. **Actions** → **General**
3. Đảm bảo:
   - ✅ "Allow all actions and reusable workflows"
   - ✅ "Allow GitHub Actions to create and approve pull requests"

### Kiểm Tra Secrets
1. **Settings** → **Secrets and variables** → **Actions**
2. Đảm bảo có secret **PAT_TOKEN** với token của bạn

## 5. Lưu Ý

- Workflow chạy **mỗi 15 phút** (theo cron schedule)
- Nếu không thấy runs, có thể:
  - Workflow chưa được enable
  - Chưa có PAT_TOKEN trong Secrets
  - RSS feed Upwork trả về lỗi (410 Gone)
  - Chưa đến lúc chạy (phải đợi đến phút chia hết cho 15)

## 6. Test Local Script

Để test script crawl hoạt động:
```bash
python .github/workflows/crawl_rss.py
```

Nếu script chạy OK nhưng không có jobs → RSS feed có thể đã thay đổi hoặc cần authentication.

