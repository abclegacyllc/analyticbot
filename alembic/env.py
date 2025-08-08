import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# --- LOYIHAMIZGA MOSLASHTIRILGAN QISM ---
# 1. Loyihamizdagi sozlamalar va modellarni import qilamiz
#    DIQQAT: 'metadata_obj' o'rniga to'g'ri nom 'metadata' ishlatilgan
from src.bot.config import settings
from src.bot.database.models import metadata
# ------------------------------------

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- LOYIHAMIZGA MOSLASHTIRILGAN QISM ---
# 2. Ma'lumotlar bazasiga ulanish manzilini to'g'ridan-to'g'ri 
#    loyihaning asosiy sozlamalaridan (.env faylidan) olamiz.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.unicode_string())

# 3. Bizning modellarimizdagi "metadata" obyektini ko'rsatamiz.
#    Alembic shu orqali jadvallarni topadi.
target_metadata = metadata
# ------------------------------------

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
