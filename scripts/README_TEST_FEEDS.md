# Hướng dẫn Test RSS Feeds

## Cách sử dụng

### 1. Test một feed đơn lẻ

```bash
python scripts/test_rss_feed.py "https://remotive.com/remote-jobs/rss-feed" --name "Remotive"
```

### 2. Test nhiều feeds từ file

Tạo file `test_feeds.yaml` (đã có sẵn):

```yaml
feeds:
  - name: "Remotive - All Remote Jobs"
    url: "https://remotive.com/remote-jobs/rss-feed"
    timeout: 10
  - name: "Himalayas - Remote Jobs"
    url: "https://himalayas.app/rss"
    timeout: 10
```

Chạy:
```bash
python scripts/test_rss_feed.py --file test_feeds.yaml
```

### 3. Export feeds OK ra config format

```bash
python scripts/test_rss_feed.py --file test_feeds.yaml --export
```

Script sẽ in ra config entries để copy vào `config/config.yaml`

## Kết quả

- ✅ **SUCCESS**: Feed OK, có thể thêm vào config
- ❌ **FAILED**: Feed lỗi (404, timeout, parse error) - KHÔNG thêm vào config
- ⚠️  **WARNING**: Feed parse được nhưng không có entries

## Ví dụ output

```
============================================================
Testing: Remotive - All Remote Jobs
URL: https://remotive.com/remote-jobs/rss-feed
============================================================
✅ SUCCESS!
   Status: 200
   Response time: 1.23s
   Feed type: rss20
   Feed title: Remotive - Remote Jobs
   Entries found: 50

   Sample entries:
   1. Senior Python Developer
      Link: https://remotive.com/remote-jobs/12345...
      Published: Mon, 27 Nov 2025 10:00:00 GMT
```

## Workflow đề xuất

1. Thêm feed mới vào `test_feeds.yaml`
2. Chạy test: `python scripts/test_rss_feed.py --file test_feeds.yaml --export`
3. Copy config entries từ output
4. Paste vào `config/config.yaml` với `enabled: true`
5. Test lại bằng cách chạy `update.bat` (chế độ 2 - chỉ sync)

