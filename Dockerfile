# 1-qadam: Asosiy Python versiyasini tanlash
FROM python:3.11-slim

# Atrof-muhit o'zgaruvchilari
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 2-qadam: Ishchi papkani o'rnatish
WORKDIR /app

# 3-qadam: Kerakli kutubxonalarni o'rnatish (caching'ni optimallashtirish uchun alohida)
# Faqat requirements.txt o'zgargandagina bu qadam qayta ishlaydi
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 4-qadam: Loyiha kodini konteynerga nusxalash
COPY . .

# 5-qadam: Alembic migratsiyalarini ishga tushirish uchun skript
# Bu skriptni docker-compose orqali chaqiramiz
# CMD ["alembic", "upgrade", "head"]
