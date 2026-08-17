import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from app.database import get_user_by_username

load_dotenv()

SECRET_KEY = os.getenv("jwt_secret_key")
if not SECRET_KEY:
    raise RuntimeError(
        "متغير البيئة jwt_secret_key غير موجود في ملف .env — "
        "أضف سطر: jwt_secret_key=\"قيمة_عشوائية_طويلة_وسرية\""
    )
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")



def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"),bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"),hashed_password.encode("utf-8"))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="التوكن غير صالح")
        user = get_user_by_username(username)
        if user is None:
            raise HTTPException(status_code=401, detail="المستخدم غير موجود")
        return user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="جلسة العمل انتهت، يرجى إعادة تسجيل الدخول",
            headers={"WWW-Authenticate": "Bearer"},
        )