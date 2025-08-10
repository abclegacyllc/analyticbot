import hmac
import hashlib
from urllib.parse import unquote

from fastapi import HTTPException

def validate_init_data(init_data: str, bot_token: str) -> dict:
    """
    Validates the initData string from a Telegram Web App.

    Args:
        init_data: The initData string from the TWA.
        bot_token: Your bot's token.

    Returns:
        A dictionary with the user data if validation is successful.

    Raises:
        HTTPException: If validation fails.
    """
    try:
        # initData'ni qismlarga ajratamiz
        data_params = sorted([
            x.split('=', 1) for x in init_data.split('&')
            if x.startswith('user=') or x.startswith('auth_date=')
        ], key=lambda x: x[0])

        # Tekshirish uchun qator (string) hosil qilamiz
        data_check_string = "\n".join([f"{k}={v}" for k, v in data_params])
        
        # initData'dan hash'ni olamiz
        received_hash = None
        for param in init_data.split('&'):
            if param.startswith('hash='):
                received_hash = param.split('=', 1)[1]
                break

        if received_hash is None:
            raise ValueError("Hash not found in initData")

        # Maxfiy kalitni yaratamiz
        secret_key = hmac.new("WebAppData".encode(), bot_token.encode(), hashlib.sha256).digest()
        
        # O'zimiz hash hisoblaymiz
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        # Ikkala hash'ni solishtiramiz
        if calculated_hash != received_hash:
            raise ValueError("Hash mismatch")

        # Foydalanuvchi ma'lumotlarini ajratib olamiz
        user_data_str = [x for x in init_data.split('&') if x.startswith('user=')][0]
        user_data_json = unquote(user_data_str.split('=', 1)[1])
        
        import json
        return json.loads(user_data_json)

    except (ValueError, IndexError, KeyError) as e:
        raise HTTPException(status_code=401, detail=f"Unauthorized: Invalid initData. {e}")