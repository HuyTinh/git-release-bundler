---
name: git-mark
description: Đánh dấu nhánh Git hiện tại (hoặc nhánh chỉ định) vào danh sách chờ release cục bộ (.git/marked_branches.txt). Dùng khi người dùng gõ /git-mark, /mark, /git-mark list, /mark list, /git-mark clear, /mark clear, /git-mark unmark <nhánh>, /mark unmark <nhánh> hoặc nói "mark nhánh này", "đánh dấu nhánh này".
---

# Git Mark Branch Skill

Kỹ năng này cho phép người dùng đánh dấu các nhánh Git trực tiếp từ khung chat của AI Agent để sau này gom Changelog và SQL Script bằng lệnh `/bundle-local`.

## Hỗ trợ các cú pháp:
- `/git-mark` hoặc `/mark`: Đánh dấu nhánh Git hiện tại đang checkout.
- `/git-mark <tên_nhánh>` hoặc `/mark <tên_nhánh>`: Đánh dấu một nhánh cụ thể (kể cả khi chưa checkout).
- `/git-mark list` hoặc `/mark list`: Xem danh sách tất cả các nhánh đã được đánh dấu.
- `/git-mark unmark <tên_nhánh>` hoặc `/mark rm <tên_nhánh>`: Gỡ 1 nhánh cụ thể ra khỏi danh sách chờ.
- `/git-mark clear` hoặc `/mark clear`: Xóa toàn bộ danh sách đã đánh dấu.

## Quy trình thực thi:
Khi người dùng gõ lệnh (ví dụ: `/git-mark`, `/mark` kèm tham số hoặc không tham số):
1. Chạy script:
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File "$HOME/.gemini/config/skills/git-mark/scripts/mark.ps1" "<action_hoac_ten_nhanh>" "<target_branch_neu_co>"
   ```
2. Phản hồi kết quả ngắn gọn, rõ ràng cho người dùng.
