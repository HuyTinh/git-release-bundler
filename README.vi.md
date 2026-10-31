# 📦 git-release-bundler

> **Bộ công cụ chuẩn bị Release cục bộ & Kỹ năng AI Agent cho Git**  
> Đánh dấu nhánh, trích xuất thay đổi, gộp script database kèm cơ chế cảnh báo an toàn SQL, và tạo Changelog 4 phần — 100% cục bộ với zero checkout, không làm rác Git remote, và zero third-party dependencies.

[![CI](https://github.com/HuyTinh/git-release-bundler/actions/workflows/ci.yml/badge.svg)](https://github.com/HuyTinh/git-release-bundler/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/HuyTinh/git-release-bundler)](https://github.com/HuyTinh/git-release-bundler/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](#)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-green.svg)](#)

[📖 Read English Documentation (README.md)](README.md)

---

## 🌟 Tại sao cần `git-release-bundler`?

Trong phát triển phần mềm hiện đại theo Agile/Sprint, các tính năng và sửa lỗi được phát triển trên nhiều nhánh độc lập (`feat/orders`, `fix/auth`, `feat/mobile-api`). Khi chuẩn bị phát hành một bản Release Candidate cho QA, Staging, hoặc Triển khai:
1. Bạn phải nhớ những nhánh nào thuộc đợt release này mà không muốn merge sớm lên nhánh chính.
2. Bạn phải tìm thủ công và nối các file migration `*.sql` nằm rải rác ở các thư mục theo đúng thứ tự.
3. Bạn cần một bản release notes sạch sẽ để gửi PO/Khách hàng, kèm danh sách API mới tách riêng cho đội Frontend & Mobile.

**`git-release-bundler` tự động hóa toàn bộ quy trình chuẩn bị release này ngay trên máy cục bộ chỉ trong vài giây.**

---

## ⚡ Tính năng nổi bật

- **100% Thuần Cục Bộ (Zero Remote Footprint)**: Không push lên remote, không sinh tag ảo, không tạo branch merge tạm bợ trên server.
- **Trích xuất Zero-Checkout (`git show`)**: Đọc commit và script database trực tiếp từ Git object database. Không bao giờ chạm vào working tree hay file đang sửa dở.
- **Changelog Chuẩn 4 Phần**:
  - **Mục 1: Tính năng & Điểm nhấn (Ready-to-copy)**: Phân 3 nhóm rõ ràng (`🚀 Features`, `🐛 Bug Fixes`, `🔧 Other Improvements`), tự động lọc bỏ tiền tố kỹ thuật và git trailers (`Co-authored-by`).
  - **Mục 2: Endpoint API Mới (Web & Mobile)**: Danh sách phẳng dạng bullet points phân theo Web và Mobile, tối ưu để copy 1 chạm dán vào Slack/Teams/Zalo.
  - **Mục 3: Database Migrations**: Liệt kê các file SQL đã gộp kèm mã băm SHA-256 và cảnh báo an toàn.
  - **Mục 4: Technical Audit**: Chi tiết mã hash commit `[%h]`, tác giả và thời gian commit nhóm theo từng nhánh.
- **Bộ Quét An Toàn SQL & Cảnh Báo Va Chạm**:
  - Tự động phát hiện các câu lệnh nguy hiểm (`DROP TABLE/DATABASE`, `TRUNCATE`, `DELETE FROM` không có `WHERE`).
  - Sắp xếp file theo thứ tự bảng chữ cái tuyệt đối để đảm bảo thứ tự chạy migration.
  - Mã băm SHA-256 tự động phát hiện và cảnh báo nếu có 2 nhánh cùng sửa một file SQL với nội dung khác nhau (`[COLLISION WARNING]`).
- **Khả Năng Kiểm Toán Tái Lập**: Ghi commit SHA và thời điểm tạo bundle vào `branches.txt`.
- **Xuất Metadata Cấu Trúc**: Tự động tạo file `release_meta.json` để tích hợp tool tự động.
- **Chế Độ Chạy Thử (`--dry-run`)**: Xem trước changelog và SQL mà không ghi file và không xóa danh sách nhánh đã mark.
- **Đa Nền Tảng & Đa Agent**: Chỉ dùng Python 3.8+ Standard Library (không cần `pip install`). Tương thích với **Antigravity**, **Claude Code**, **Cursor**, **Windsurf** và Terminal.

---

## 🚀 Cài đặt nhanh

### 1. Clone repository
```bash
git clone https://github.com/HuyTinh/git-release-bundler.git
cd git-release-bundler
```

### 2. Chạy bộ cài đặt 1-Click

#### Trên Windows (PowerShell):
```powershell
./install.ps1
```

#### Trên macOS / Linux (Bash / Zsh):
```bash
chmod +x install.sh
./install.sh
```

Bộ cài đặt tự động kiểm tra Python >= 3.8, sao chép skills vào `~/.gemini/config/skills/` (và `~/.claude/skills/` nếu có Claude Code), đồng thời cấu hình Git alias toàn cục (`git mark`, `git bundle-local`).

*(Để gỡ cài đặt sạch sẽ bất cứ lúc nào: `./uninstall.ps1` hoặc `./uninstall.sh`)*

---

## 📖 Hướng dẫn sử dụng

### 1. Trên Terminal

```bash
# 1. Đánh dấu nhánh bạn vừa làm xong:
git mark

# Hoặc đánh dấu một nhánh cụ thể mà không cần checkout:
git mark feat/orders-export

# 2. Xem danh sách các nhánh đang chờ release:
git mark list

# 3. Bỏ đánh dấu một nhánh:
git mark unmark feat/orders-export

# 4. Xóa sạch danh sách đã đánh dấu:
git mark clear

# 5. Gom và đóng gói release:
git bundle-local uat-1.2.0

# Các cờ tùy chọn hữu ích:
# Chạy thử xem trước mà không ghi file ra đĩa:
git bundle-local uat-1.2.0 --dry-run

# Ghi đè release từ đầu (không gộp nhánh cũ):
git bundle-local uat-1.2.0 --fresh

# Chỉ định nhánh gốc đối chiếu (mặc định: develop hoặc main):
git bundle-local uat-1.2.0 --base staging
```

---

### 2. Trong AI Agent Chat (Antigravity / Claude Code)

| Lệnh Chat | Mô tả |
| :--- | :--- |
| `/git-mark` hoặc `/mark` | Đánh dấu nhánh hiện tại |
| `/git-mark <branch_name>` | Đánh dấu một nhánh cụ thể |
| `/git-mark list` | Hiển thị danh sách nhánh đã mark có đánh số |
| `/git-mark unmark <branch>` | Gỡ một nhánh khỏi danh sách |
| `/git-mark clear` | Xóa sạch danh sách đã mark |
| `/bundle-local <version>` | Gom release (ví dụ: `/bundle-local uat-1.2.0`) |
| `/bundle-local <version> --dry-run` | Chạy thử xem trước kết quả |
| `/bundle-local <version> --fresh` | Ghi đè làm mới release từ đầu |

---

## 📂 Cấu trúc thư mục đầu ra

```text
release_output/
└── uat-1.2.0/
    ├── branches.txt                <-- Danh sách nhánh kèm commit SHA & thời gian
    ├── CHANGELOG_LOCAL.md          <-- Changelog chuẩn 4 phần (Features, APIs, DB, Audit)
    ├── combined_db_scripts.sql     <-- File SQL tổng hợp kèm header an toàn
    └── release_meta.json           <-- Metadata định dạng JSON
```

*(Nếu repo có thư mục `.antigravity`, kết quả sẽ được lưu tại `.antigravity/release_output/` và tự động được exclude khỏi git via `.git/info/exclude`)*.

👉 Xem thư mục [examples/](examples/) để xem trực tiếp các file mẫu thực tế!

---

## 🤖 Tích hợp Cursor IDE (.cursor/rules/)

Đối với người dùng Cursor, chỉ cần sao chép file `.cursor/rules/release-bundler.mdc` vào thư mục `.cursor/rules/` trong dự án của bạn để Cursor Agent tự động hiểu và sử dụng bộ lệnh này.

---

## 🔒 An toàn & Giới hạn

### Bộ quét an toàn SQL
`git-release-bundler` chủ động phân tích các câu lệnh SQL có nguy cơ gây thảm họa dữ liệu (`DROP TABLE/DATABASE`, `TRUNCATE`, `DELETE FROM` thiếu `WHERE`). Nếu phát hiện, một banner cảnh báo đỏ sẽ được chèn ngay ở đầu file `combined_db_scripts.sql`.

### Giới hạn
1. **Yêu cầu local branch**: Nhánh phải có trên máy cục bộ (nếu chỉ có trên remote, hãy chạy `git checkout --track origin/<branch>`).
2. **Ngữ cảnh Git**: Bắt buộc phải chạy trong một Git repository.
3. **Không tự động thực thi Database**: Tool chỉ đóng gói và kiểm tra script; không tự ý kết nối hay chạy SQL vào database thật.

---

## 📄 Bản quyền & Tác giả
Phát hành theo giấy phép [MIT License](LICENSE).  
Tác giả: [HuyTinh](https://github.com/HuyTinh)
