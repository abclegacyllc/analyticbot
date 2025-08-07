import asyncio
from aiogram import Bot

# DIQQAT: .env faylingizdagi bot tokenini shu yerga qo'ying
BOT_TOKEN = "7900046521:AAGgnLxHfXuKMfR0u1Fn6V6YliPnywkUu9E"

async def main():
    print(f"Attempting to clear webhook for bot with token ending in ...{BOT_TOKEN[-6:]}")
    bot = Bot(token=BOT_TOKEN)
    try:
        # Webhook'ni o'chiramiz va kutilayotgan yangilanishlarni tozalaymiz
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook muvaffaqiyatli o'chirildi.")
        print("Endi botni polling rejimida ishga tushirishingiz mumkin.")
    except Exception as e:
        print(f"❌ Xatolik yuz berdi: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
