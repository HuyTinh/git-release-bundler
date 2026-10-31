-- ======================================================================
-- COMBINED DATABASE RELEASE SCRIPT: uat-1.2.0
-- Generated at: 2026-10-31 17:50:00
-- Source branches: feat/orders-export, fix/auth-deadlock
-- Source files & SHA-256 Checksums:
--   * migrations/01_export_jobs.sql [sha256: 4b2c1d0e9f8a7b6c...]
--   * migrations/02_payment_retry.sql [sha256: e5f4d3c2b1a09f8e...]
-- ======================================================================

-- ----------------------------------------------------------------------
-- FILE: migrations/01_export_jobs.sql
-- SOURCE BRANCH: feat/orders-export
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS export_jobs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    file_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------
-- FILE: migrations/02_payment_retry.sql
-- SOURCE BRANCH: fix/auth-deadlock
-- ----------------------------------------------------------------------
ALTER TABLE payment_transactions ADD COLUMN retry_count INT DEFAULT 0;
CREATE INDEX idx_payment_status_retry ON payment_transactions (status, retry_count);
