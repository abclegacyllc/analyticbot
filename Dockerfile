# Dockerfile'ning to'liq va tuzatilgan versiyasi

# 1-bosqich: Python bog'liqliklarini o'rnatish
FROM python:3.11-slim as builder

WORKDIR /app

# Poetry o'rnatish
RUN pip install poetry

# Bog'liqlik fayllarini nusxalash
COPY poetry.lock pyproject.toml /app/

# Bog'liqliklarni o'rnatish (development uchun kerak emaslarini o'tkazib yuborish)
RUN poetry install --no-dev

# 2-bosqich: Asosiy ilovani yaratish
FROM python:3.11-slim

WORKDIR /app

# Birinchi bosqichdan virtual muhitni nusxalash
COPY --from=builder /app/.venv /.venv

# PATH o'zgaruvchisiga virtual muhitni qo'shish
ENV PATH="/app/.venv/bin:$PATH"

# --- O'ZGARTIRILGAN QATOR ---
# Butun loyiha kodini nusxalash
COPY . .

# Bot, API yoki Celery ishchisini ishga tushirish uchun kirish nuqtasi
# Bu buyruq docker-compose.yml faylida bekor qilinadi (override)
CMD ["python", "run_bot.py"]
