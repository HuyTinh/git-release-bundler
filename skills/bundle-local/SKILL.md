---
name: bundle-local
description: Gom Changelog và file Script Database tổng hợp từ các nhánh Git đã được mark trên local, đặt vào thư mục phiên bản (.antigravity/release_output/<version>/ hoặc release_output/<version>/). Dùng khi người dùng yêu cầu gom nhánh, generate changelog, tạo bản release local, hoặc gõ /bundle-local <version>.
---

# Bundle Local Release Skill

Kỹ năng này tự động hóa việc gom các commit thành `CHANGELOG_LOCAL.md` (chuẩn format 2 tầng: Product Release Notes & Technical Audit) và gộp các script SQL thành `combined_db_scripts.sql` từ danh sách các nhánh Git đã được mark (trong `.git/marked_branches.txt`). Áp dụng tổng quát (General-purpose) cho mọi dự án và mọi ngôn ngữ lập trình.

## Nguyên tắc cốt lõi:
- **100% Local**: Tuyệt đối không tương tác với remote, không tạo tag, không tạo nhánh mới, không push.
- **Zero Checkout**: Không bao giờ checkout sang các nhánh khác để tránh làm bẩn hoặc xung đột các file chưa commit của người dùng.
- **Format Changelog 2 tầng chuẩn công nghiệp (2-Tier Standard)**:
  - Tầng 1: Danh sách tính năng/thay đổi ngắn gọn, thân thiện với Product/QA/PO (Ready-to-copy).
  - Tầng 2: Bảng tra cứu commit kỹ thuật theo từng nhánh (Technical Audit cho Developers).
- **Vị trí Output**:
  - Nếu dự án có `.antigravity/` $\rightarrow$ lưu tại `.antigravity/release_output/<version>/`
  - Nếu không có `.antigravity/` $\rightarrow$ lưu tại `release_output/<version>/`

## Các tính năng thông minh:
- **Smart Accumulate (Mặc định)**: Nếu version đã tồn tại, tự động gộp các nhánh cũ + nhánh mới bổ sung để tái tạo bản release đầy đủ.
- **Chế độ Fresh (`-fresh` hoặc `-clean`)**: Nếu muốn xóa sạch làm lại từ đầu phiên bản đó mà không gộp nhánh cũ: `/bundle-local <version> -fresh`.
- **Tự động nhận diện Base**: Ưu tiên theo thứ tự `develop` $\rightarrow$ `dev` $\rightarrow$ `main` $\rightarrow$ `master` (hoặc truyền custom base: `/bundle-local <version> <base_branch>`).
- **Lọc file đã xóa (`--diff-filter=ACMR`)**: Không bao giờ nhặt phải các file SQL đã bị xóa/đổi tên trên nhánh.

## Cách thực thi khi người dùng kích hoạt:
Khi người dùng gõ `/bundle-local [version] [flags]` hoặc yêu cầu gom các nhánh đã mark:
1. Lấy tham số `version` và cờ (nếu có):
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File "$HOME/.gemini/config/skills/bundle-local/scripts/bundle-local.ps1" "<version>" "<flags>"
   ```
2. Đọc nội dung file `CHANGELOG_LOCAL.md` vừa được tạo:
   - Trích xuất phần **Danh sách thay đổi & Tính năng (Ready-to-copy)** hiển thị ngay trong khung chat dưới dạng block code / danh sách để người dùng có thể bấm copy 1-click.
   - Kèm theo đường dẫn file `combined_db_scripts.sql` và số lượng file SQL đã gom.
