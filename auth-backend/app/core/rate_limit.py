from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config.settings import settings

limiter = Limiter(key_func=get_remote_address)

login_limiter = limiter.limit(settings.LOGIN_RATE_LIMIT)
forgot_password_limiter = limiter.limit(settings.FORGOT_PASSWORD_RATE_LIMIT)
