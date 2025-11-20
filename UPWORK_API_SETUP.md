# Upwork API Setup - Thay Thế RSS Feed

## ⚠️ Vấn Đề

Upwork đã **chính thức ngừng hỗ trợ RSS feed** từ ngày **20 tháng 8 năm 2024**. 
RSS endpoint trả về **410 (Gone)**.

## ✅ Giải Pháp: Dùng Upwork API

### Bước 1: Request API Key

1. Vào: https://support.upwork.com/hc/en-us/articles/17995842326931--Request-an-API-key
2. Điền form request API key:
   - **Profile**: Phải có profile hoàn chỉnh trên Upwork
   - **Purpose**: Mô tả ngắn gọn mục đích sử dụng (ví dụ: "Automated job search and proposal management")
   - **Use case**: Giải thích cách bạn sẽ dùng API
3. Submit và đợi Upwork approve (thường 1-3 ngày)

### Bước 2: Setup OAuth 2.0

Upwork API sử dụng **OAuth 2.0** để authenticate:

1. Tạo OAuth App trên Upwork Developer Portal
2. Lấy **Client ID** và **Client Secret**
3. Setup redirect URI
4. Lấy **Access Token** và **Refresh Token**

### Bước 3: Cấu Hình

Thêm vào `config/config.yaml`:

```yaml
upwork_api:
  client_id: "YOUR_CLIENT_ID"
  client_secret: "YOUR_CLIENT_SECRET"
  access_token: "YOUR_ACCESS_TOKEN"
  refresh_token: "YOUR_REFRESH_TOKEN"
  base_url: "https://www.upwork.com/api"
```

### Bước 4: Update Script

Script sẽ cần update để:
- Dùng OAuth 2.0 authentication
- Gọi Upwork API endpoints thay vì RSS
- Handle rate limits và pagination

## 📚 Tài Liệu API

- **API Documentation**: https://developers.upwork.com/
- **Authentication**: https://support.upwork.com/hc/en-us/articles/115015933448-API-authentication-and-security
- **Job Search API**: https://developers.upwork.com/api-docs#jobs

## 🔄 Alternative: UpNotify Service

Nếu không muốn dùng API, có thể dùng service **UpNotify**:
- Website: https://upnotify.me/
- Cung cấp notification về jobs mới
- Có thể integrate vào hệ thống

## ⚡ Quick Fix Tạm Thời

Trong khi chờ API key, có thể:
1. **Manual crawl**: Copy jobs từ Upwork search page
2. **Browser extension**: Dùng extension để export jobs
3. **Test với sample data**: Tạo file `data/raw_jobs.jsonl` mẫu để test hệ thống

## 📝 Lưu Ý

- API có **rate limits** - cần implement retry logic
- Access token **expires** - cần refresh token tự động
- API chỉ trả về jobs **public** - không có private jobs
- Cần tuân thủ **Upwork Terms of Service**

