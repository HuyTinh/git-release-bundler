# 📦 git-release-bundler

> **Universal Local Release Toolkit & AI Agent Skills for Git**  
> Mark branches, extract changes, compile combined database scripts, and generate 2-tier release notes — 100% locally with zero checkouts and zero remote clutter.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Cross--Agent-green.svg)](#)

---

## 🌟 Tại sao cần `git-release-bundler`? (Why?)

Khi làm việc trong các dự án thực tế (đặc biệt là theo mô hình Agile/Sprint), các tính năng thường được phát triển trên nhiều nhánh độc lập (`feat/order`, `feat/payment`, `fix/auth`). Đến ngày đóng gói release hoặc bàn giao UAT/Staging:
1. Bạn phải tự nhớ xem đợt này release những nhánh nào.
2. Bạn phải lục từng nhánh để copy các file migration SQL (`*.sql`) rồi ghép thủ công thành 1 file chạy DB.
3. Bạn phải tổng hợp commit message từ nhiều nhánh để viết Release Changelog gửi PO/QA.
4. Bạn không muốn tạo nhánh merge lung tung hay push tag rác lên remote Git.

**`git-release-bundler` giải quyết trọn vẹn quy trình này chỉ với 2 lệnh!**

---

## ⚡ Tính năng nổi bật (Features)

- **100% Thuần Local (Zero Remote Footprint)**: Không push remote, không tạo tag, không tạo nhánh merge ảo.
- **Không bao giờ Checkout (`git show` engine)**: Đọc commit và trích xuất file SQL trực tiếp từ Git Object Database. Không làm bẩn working tree hay conflict code đang viết dở.
- **Format Changelog 2 tầng chuẩn công nghiệp**:
  - **Tầng 1 (Ready-to-copy)**: Tự động loại bỏ tiền tố kỹ thuật (`feat:`, `fix:`, `[TICKET-123]`) và khử trùng lặp $\rightarrow$ Dạng gạch đầu dòng nghiệp vụ sạch sẽ để gửi ngay cho PO/QA/Khách hàng.
  - **Tầng 2 (Technical Audit)**: Lưu đầy đủ commit hash `[%h]`, tác giả và thời gian để dev tra cứu.
- **Ghép Database Scripts thông minh**: Tự động gom đệ quy mọi file `*.sql` phát sinh trên các nhánh, bọc comment nguồn gốc rõ ràng, tự động loại bỏ các file đã bị xóa (`--diff-filter=ACMR`).
- **Smart Accumulate**: Nếu phát hiện thiếu nhánh sau khi đã tạo release, chỉ cần mark thêm nhánh mới và trigger lại cùng tên phiên bản $\rightarrow$ Tự động gộp nhánh cũ + mới. Có cờ `-fresh` nếu muốn làm mới từ đầu.
- **Đa nền tảng AI Agent**: Chạy mượt mà trên cả **Terminal** lẫn trong **Chat của AI Agent** (Antigravity, Claude Code, Cursor, Windsurf, Cline...).

---

## 🚀 Cài đặt nhanh (Quick Installation)

Mở PowerShell tại thư mục repo và chạy:

```powershell
./install.ps1
```

Script sẽ tự động:
1. Copy các skill vào thư mục `~/.gemini/config/skills/`.
2. Đăng ký các Git Alias toàn cục (`git mark`, `git bundle-local`).

*(Muốn gỡ cài đặt sạch sẽ bất cứ lúc nào: `./uninstall.ps1`)*

---

## 📖 Hướng dẫn sử dụng (Usage)

### Cách 1: Sử dụng trong Terminal (PowerShell / Git Bash)

```bash
# 1. Đang đứng ở nhánh nào muốn release, chỉ cần gõ:
git mark

# Hoặc đánh dấu một nhánh cụ thể kể cả khi chưa checkout:
git mark feat/order-service

# 2. Xem danh sách các nhánh đang chờ:
git mark list

# 3. Gỡ bớt 1 nhánh ra khỏi danh sách nếu cần:
git mark unmark feat/order-service

# 4. Gom Changelog và Database Script vào thư mục phiên bản:
git bundle-local uat-1.1.3

# (Tùy chọn: Làm mới hoàn toàn phiên bản đó, không gộp nhánh cũ)
git bundle-local uat-1.1.3 -fresh
```

---

### Cách 2: Sử dụng trong Chat với AI Agent (Antigravity / Gemini CLI)

| Lệnh Chat | Chức năng |
| :--- | :--- |
| `/git-mark` hoặc `/mark` | Đánh dấu nhánh hiện tại |
| `/git-mark <tên_nhánh>` | Đánh dấu nhánh chỉ định |
| `/git-mark list` | Hiển thị danh sách các nhánh đang chờ |
| `/git-mark unmark <nhánh>` | Gỡ 1 nhánh ra khỏi danh sách |
| `/git-mark clear` | Xóa sạch danh sách |
| `/bundle-local <version>` | Kích hoạt gom release (VD: `/bundle-local uat-1.1.3`) |

---

## 📂 Cấu trúc kết quả sinh ra (Output Artifacts)

```text
# Nếu repo có thư mục .antigravity:
.antigravity/
└── release_output/
    └── uat-1.1.3/                      <-- Tên phiên bản bạn truyền vào
        ├── branches.txt                <-- Danh sách các nhánh cấu thành bản này
        ├── CHANGELOG_LOCAL.md          <-- Changelog 2 tầng (Ready-to-copy & Audit)
        └── combined_db_scripts.sql     <-- File SQL tổng hợp toàn bộ migration

# Nếu repo thông thường:
release_output/
└── uat-1.1.3/
    ├── branches.txt
    ├── CHANGELOG_LOCAL.md
    └── combined_db_scripts.sql
```

---

## 🤖 Tương thích với các AI Agent khác (Cross-Agent Setup)

- **Claude Code**: Copy thư mục `skills/*` vào `~/.claude/skills/`.
- **Cursor / Windsurf**: Thêm dòng sau vào `.cursorrules`:
  ```text
  When I type /bundle-local <version>, run PowerShell:
  powershell -NoProfile -ExecutionPolicy Bypass -File "$HOME/.gemini/config/skills/bundle-local/scripts/bundle-local.ps1" "<version>"
  ```
- **CLI thuần túy**: Sử dụng trực tiếp `git mark` và `git bundle-local` mà không cần bất kỳ AI Agent nào.

---

## 📄 License
Phát hành theo giấy phép [MIT License](LICENSE).
Tác giả: [HuyTinh](https://github.com/HuyTinh).
