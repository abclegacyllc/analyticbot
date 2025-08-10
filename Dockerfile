# 1-BOSQICH: Bog'liqliklarni aniqlash va qotirish (lock)
FROM python:3.11-slim as builder

# Poetry'ni o'rnatish
WORKDIR /opt/poetry
RUN pip install poetry==1.8.2

# FAQAT pyproject.toml faylini nusxalash
COPY pyproject.toml poetry.lock* ./

# Eng muhim qadam: poetry.lock faylini qayta yaratib,
# pyproject.toml bilan mosligini ta'minlash
RUN poetry lock --no-update

# requirements.txt faylini yaratish
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes


# 2-BOSQICH: Asosiy ilovani qurish
FROM python:3.11-slim

WORKDIR /app

# Birinchi bosqichdan tayyor requirements.txt faylini nusxalash
COPY --from=builder /opt/poetry/requirements.txt .

# Bog'liqliklarni pip orqali o'rnatish
RUN pip install --no-cache-dir -r requirements.txt

# Loyihaning qolgan qismini nusxalash
COPY . .

# Konteyner ishga tushganda bajariladigan buyruq
CMD ["python", "run_bot.py"]
