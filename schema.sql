-- ============================================================
-- Schema Database: Aplikasi Manajemen Keuangan Pribadi
-- ============================================================
--
-- Cara menjalankan:
--   mysql -u root -p < schema.sql
--
-- Atau dari MySQL shell:
--   source /path/ke/schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS finance_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE finance_db;

-- ------------------------------------------------------------
-- Tabel: categories
-- Menyimpan kategori pemasukan (income) dan pengeluaran (expense)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
    id   INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(100)  NOT NULL,
    type ENUM('income','expense') NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_category_name_type (name, type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Tabel: transactions
-- Menyimpan setiap transaksi keuangan
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transactions (
    id               INT UNSIGNED   NOT NULL AUTO_INCREMENT,
    category_id      INT UNSIGNED   NOT NULL,
    type             ENUM('income','expense') NOT NULL,
    amount           DECIMAL(15, 2) NOT NULL CHECK (amount > 0),
    description      VARCHAR(255)   NOT NULL DEFAULT '',
    transaction_date DATE           NOT NULL,
    created_at       DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_trx_date        (transaction_date),
    KEY idx_trx_month_year  (transaction_date),
    KEY idx_trx_category    (category_id),
    CONSTRAINT fk_trx_category
        FOREIGN KEY (category_id) REFERENCES categories (id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Tabel: budgets
-- Menyimpan anggaran bulanan per kategori (upsert-safe via UNIQUE)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS budgets (
    id          INT UNSIGNED   NOT NULL AUTO_INCREMENT,
    category_id INT UNSIGNED   NOT NULL,
    month       TINYINT        NOT NULL CHECK (month BETWEEN 1 AND 12),
    year        SMALLINT       NOT NULL CHECK (year BETWEEN 2000 AND 2100),
    amount      DECIMAL(15, 2) NOT NULL CHECK (amount > 0),
    PRIMARY KEY (id),
    UNIQUE KEY uq_budget_cat_month_year (category_id, month, year),
    CONSTRAINT fk_budget_category
        FOREIGN KEY (category_id) REFERENCES categories (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Data awal: kategori bawaan
-- (opsional, hapus bila ingin database kosong)
-- ------------------------------------------------------------
INSERT IGNORE INTO categories (name, type) VALUES
    -- Pemasukan
    ('Gaji',              'income'),
    ('Freelance',         'income'),
    ('Investasi',         'income'),
    ('Bonus',             'income'),
    ('Lain-lain Masuk',   'income'),
    -- Pengeluaran
    ('Makanan & Minuman', 'expense'),
    ('Transportasi',      'expense'),
    ('Tagihan & Utilitas','expense'),
    ('Belanja',           'expense'),
    ('Kesehatan',         'expense'),
    ('Hiburan',           'expense'),
    ('Pendidikan',        'expense'),
    ('Tabungan',          'expense'),
    ('Lain-lain Keluar',  'expense');
