import os

from dotenv import load_dotenv

load_dotenv()


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} belum diatur. Salin .env.example ke .env lalu isi nilainya.")
    return value


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": _require_env("DB_PASSWORD"),
    "database": os.getenv("DB_NAME", "finance_db"),
}
