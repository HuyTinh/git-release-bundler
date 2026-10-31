# Release Changelog: uat-1.2.0
- **Created at:** 2026-10-31 17:50:00
- **Base branch:** `develop`
- **Branch count:** 2

---

### 1. Features & Business Highlights (Ready-to-copy):

#### 🚀 Features:
- Add bulk order export to Excel format
- Create export status notification badge

#### 🐛 Bug Fixes:
- Resolve token expiration deadlock in authentication flow

#### 🔧 Other Improvements:
- Bump dependencies and format migration queries

---

### 2. New API Endpoints:

**Web:**
- `POST /api/v1/orders/export-excel` - Xuất báo cáo đơn hàng ra Excel

**Mobile:**
- `POST /api/v1/mobile/payments/vnpay/retry` - Thử lại thanh toán VNPay

---

### 3. Database Migrations:
- `combined_db_scripts.sql` (2 files compiled: 01_export_jobs.sql, 02_payment_retry.sql)

---

### 4. Technical Audit (Commits by branch):

#### Branch: `feat/orders-export`
- [3f1a2b4] feat(order): add bulk order export to Excel format *(HuyTinh, 2 hours ago)*
- [7e8d9c0] feat(ui): create export status notification badge *(HuyTinh, 1 hour ago)*

#### Branch: `fix/auth-deadlock`
- [8d7c6e5] fix(auth)!: resolve token expiration deadlock in authentication flow *(DevB, 1 day ago)*
- [4a5b6c7] chore(deps): bump dependencies and format migration queries *(DevB, 1 day ago)*
