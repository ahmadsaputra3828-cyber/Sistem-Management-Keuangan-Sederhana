"""
Modul akses database MySQL untuk aplikasi manajemen keuangan.
Semua query terpusat di sini supaya UI (main.py / ui/*) tidak perlu tahu detail SQL.

Setiap fungsi membuka koneksi dari pool, mengerjakan satu operasi, lalu menutup
koneksi (connection pooling membuatnya murah). Pola ini dipertahankan apa adanya
dari versi awal karena sudah bekerja dan sederhana untuk dibaca.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from mysql.connector import pooling

from config import DB_CONFIG

_pool: pooling.MySQLConnectionPool | None = None


def get_pool() -> pooling.MySQLConnectionPool:
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="finance_pool",
            pool_size=5,
            **DB_CONFIG,
        )
    return _pool


def get_connection():
    return get_pool().get_connection()


def test_connection() -> tuple[bool, str | None]:
    """Coba konek ke DB. Return (True, None) jika sukses, (False, pesan_error) jika gagal."""
    try:
        conn = get_connection()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# KATEGORI
# ---------------------------------------------------------------------------

def get_categories(type_: str | None = None) -> list[dict[str, Any]]:
    """Ambil semua kategori, opsional difilter berdasarkan type ('income'/'expense')."""
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        if type_:
            cur.execute(
                "SELECT id, name, type FROM categories WHERE type=%s ORDER BY name",
                (type_,),
            )
        else:
            cur.execute("SELECT id, name, type FROM categories ORDER BY type, name")
        return cur.fetchall()
    finally:
        conn.close()


def add_category(name: str, type_: str) -> int:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO categories (name, type) VALUES (%s, %s)",
            (name.strip(), type_),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def delete_category(category_id: int) -> None:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM categories WHERE id=%s", (category_id,))
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# TRANSAKSI
# ---------------------------------------------------------------------------

def add_transaction(
    category_id: int, type_: str, amount: Decimal, description: str, transaction_date: date,
) -> int:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO transactions (category_id, type, amount, description, transaction_date)
               VALUES (%s, %s, %s, %s, %s)""",
            (category_id, type_, amount, description, transaction_date),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_transaction(
    trx_id: int, category_id: int, type_: str, amount: Decimal,
    description: str, transaction_date: date,
) -> None:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """UPDATE transactions
               SET category_id=%s, type=%s, amount=%s, description=%s, transaction_date=%s
               WHERE id=%s""",
            (category_id, type_, amount, description, transaction_date, trx_id),
        )
        conn.commit()
    finally:
        conn.close()


def delete_transaction(trx_id: int) -> None:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM transactions WHERE id=%s", (trx_id,))
        conn.commit()
    finally:
        conn.close()


def get_transactions(
    month: int | None = None, year: int | None = None, limit: int = 500,
) -> list[dict[str, Any]]:
    """Ambil daftar transaksi, opsional difilter per bulan & tahun, terbaru dulu."""
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        query = """
            SELECT t.id, t.type, t.amount, t.description, t.transaction_date,
                   c.id AS category_id, c.name AS category_name
            FROM transactions t
            JOIN categories c ON c.id = t.category_id
        """
        params: list[Any] = []
        if month and year:
            query += " WHERE MONTH(t.transaction_date)=%s AND YEAR(t.transaction_date)=%s"
            params += [month, year]
        query += " ORDER BY t.transaction_date DESC, t.id DESC LIMIT %s"
        params.append(limit)
        cur.execute(query, params)
        return cur.fetchall()
    finally:
        conn.close()


def get_summary(month: int, year: int) -> dict[str, Any]:
    """Total pemasukan & pengeluaran untuk bulan & tahun tertentu."""
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN type='income' THEN amount ELSE 0 END), 0) AS total_income,
                COALESCE(SUM(CASE WHEN type='expense' THEN amount ELSE 0 END), 0) AS total_expense
            FROM transactions
            WHERE MONTH(transaction_date)=%s AND YEAR(transaction_date)=%s
            """,
            (month, year),
        )
        return cur.fetchone()
    finally:
        conn.close()


def get_expense_by_category(month: int, year: int) -> list[dict[str, Any]]:
    """Total pengeluaran per kategori untuk bulan & tahun tertentu (dipakai di dashboard & anggaran)."""
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT c.id AS category_id, c.name AS category_name,
                   COALESCE(SUM(t.amount), 0) AS total_spent
            FROM categories c
            LEFT JOIN transactions t
                ON t.category_id = c.id
                AND t.type = 'expense'
                AND MONTH(t.transaction_date) = %s
                AND YEAR(t.transaction_date) = %s
            WHERE c.type = 'expense'
            GROUP BY c.id, c.name
            ORDER BY c.name
            """,
            (month, year),
        )
        return cur.fetchall()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# ANGGARAN (BUDGET)
# ---------------------------------------------------------------------------

def set_budget(category_id: int, month: int, year: int, amount: Decimal) -> None:
    """Set/update anggaran untuk kategori di bulan & tahun tertentu (upsert)."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO budgets (category_id, month, year, amount)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE amount = VALUES(amount)
            """,
            (category_id, month, year, amount),
        )
        conn.commit()
    finally:
        conn.close()


def delete_budget(budget_id: int) -> None:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM budgets WHERE id=%s", (budget_id,))
        conn.commit()
    finally:
        conn.close()


def get_budget_progress(month: int, year: int) -> list[dict[str, Any]]:
    """
    Anggaran vs realisasi pengeluaran per kategori untuk bulan & tahun tertentu.
    Hanya mengembalikan kategori yang sudah punya anggaran di-set.
    """
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT
                b.id AS budget_id,
                c.id AS category_id,
                c.name AS category_name,
                b.amount AS budget_amount,
                COALESCE(SUM(t.amount), 0) AS spent_amount
            FROM budgets b
            JOIN categories c ON c.id = b.category_id
            LEFT JOIN transactions t
                ON t.category_id = c.id
                AND t.type = 'expense'
                AND MONTH(t.transaction_date) = b.month
                AND YEAR(t.transaction_date) = b.year
            WHERE b.month = %s AND b.year = %s
            GROUP BY b.id, c.id, c.name, b.amount
            ORDER BY c.name
            """,
            (month, year),
        )
        return cur.fetchall()
    finally:
        conn.close()
