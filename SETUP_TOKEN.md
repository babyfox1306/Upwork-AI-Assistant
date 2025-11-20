# Setup GitHub Personal Access Token

Để GitHub Actions có thể commit và push jobs mới vào repo, bạn cần setup Personal Access Token (PAT).

## Bước 1: Tạo Token trên GitHub

1. Vào GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Đặt tên token (ví dụ: "Upwork AI Assistant")
4. Chọn scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `workflow` (Update GitHub Action workflows)
5. Click "Generate token"
6. **Copy token ngay** (chỉ hiển thị 1 lần): `ghp_...`

## Bước 2: Thêm Token vào GitHub Secrets

**Token của bạn:** `[Paste token của bạn vào đây - không commit token thật vào repo]`

1. Vào repo của bạn trên GitHub
2. Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `PAT_TOKEN`
5. Value: Paste token ở trên
6. Click "Add secret"

**Lưu ý:** Token này là fine-grained token (`github_pat_...`), cần đảm bảo có quyền:
- ✅ `Contents: Write` (để commit/push)
- ✅ `Workflows: Write` (để update workflows)

## Bước 3: Verify

Sau khi setup, GitHub Actions workflow sẽ tự động:
- Crawl RSS Upwork mỗi 15 phút
- Commit và push jobs mới vào `data/raw_jobs.jsonl`

Kiểm tra trong tab **Actions** của repo để xem workflow có chạy thành công không.

## Lưu ý

- Token này chỉ dùng cho GitHub Actions, không commit vào code
- Nếu token hết hạn, tạo token mới và update secret `PAT_TOKEN`
- Token có quyền `repo` nên có thể commit/push vào private repo

