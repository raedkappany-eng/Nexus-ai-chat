import os
import uuid
import asyncio
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.database import (
    get_all_messages_row,
    save_message,
    get_recent_messages,
    init_db,
    get_user_by_username,
    create_user,
    get_connection
)
from app.ai_services import (ask_gemini, 
                             ask_mistral_vision,
                             ask_mistral_small,
                             ask_mistral_code,
                             _ask_mistral_api)
from app.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

app = FastAPI()


_origins_env = os.getenv("allowed_origins", "")
ALLOWED_ORIGINS = [o.strip() for o in _origins_env.split(",") if o.strip()] or [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

ALLOWED_CONTENT_TYPES = {
    "image/png", "image/jpeg", "image/webp", "image/gif",
    "application/pdf", "text/plain",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # 15MB

init_db()


class UserRegister(BaseModel):
    username: str
    password: str

    class Config:
        str_strip_whitespace = True


class Attachment(BaseModel):
    url: str
    filename: str
    content_type: str


class ChatPrompt(BaseModel):
    prompt: str
    target_bot: str = "all"
    attachment: Attachment | None = None


@app.get("/favicon.ico")
async def favicon():
    from fastapi.responses import Response
    return Response(status_code=204)


@app.get("/")
async def serve_index():
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "index.html not found"}


@app.post("/api/register")
def register(user: UserRegister):
    if len(user.username.strip()) < 3 or len(user.password) < 4:
        raise HTTPException(
            status_code=400,
            detail="اسم المستخدم يجب أن يكون 3 أحرف على الأقل وكلمة المرور 4 أحرف على الأقل"
        )

    hashed = hash_password(user.password)
    user_id = create_user(user.username, hashed)

    if not user_id:
        raise HTTPException(status_code=400, detail="اسم المستخدم مستخدم بالفعل، اختر اسمًا آخر")

    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer", "username": user.username}


@app.post("/api/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="اسم المستخدم أو كلمة المرور غير صحيحة")

    token = create_access_token({"sub": user["username"]})
    return {"access_token": token, "token_type": "bearer", "username": user["username"]}


@app.get("/api/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return {"username": current_user["username"], "id": current_user["id"]}


@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="نوع الملف غير مدعوم. الأنواع المسموحة: صور، PDF، نص، Word",
        )

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=400,
            detail="حجم الملف أكبر من الحد المسموح (15 ميجابايت)",
        )

    original_name = file.filename or "file"
    extension = os.path.splitext(original_name)[1][:10]
    safe_name = f"{uuid.uuid4().hex}{extension}"
    dest_path = os.path.join(UPLOADS_DIR, safe_name)

    with open(dest_path, "wb") as f:
        f.write(contents)

    file_url = f"/uploads/{safe_name}"

    return {
        "url": file_url,
        "filename": original_name,
        "content_type": file.content_type,
        "size": len(contents),
    }


@app.get("/api/messages")
async def get_messages(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT sender, content, timestamp FROM messages WHERE user_id = ? ORDER BY id ASC",
            (user_id,)
        )
        rows = cursor.fetchall()
        return [{"sender": r[0], "content": r[1], "timestamp": r[2]} for r in rows]
    except Exception as e:
        print(f"Error fetching messages: {e}")
        return []
    finally:
        conn.close()


@app.post("/api/chat")
async def chat_endpoint(data: ChatPrompt, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    username = current_user["username"]
    prompt = data.prompt
    target_bot = data.target_bot.lower()

    try:
        
        stored_content = prompt
        prompt_for_ai = prompt
        image_bytes = None
        image_mime = None

        if data.attachment:
            stored_content = (
                f"{prompt}\n[ATTACHMENT]{data.attachment.url}|"
                f"{data.attachment.filename}|{data.attachment.content_type}[/ATTACHMENT]"
            )

            is_image = (data.attachment.content_type or "").startswith("image/")
            if is_image:
                local_name = os.path.basename(data.attachment.url)
                local_path = os.path.join(UPLOADS_DIR, local_name)
                if os.path.isfile(local_path):
                    with open(local_path, "rb") as f:
                        image_bytes = f.read()
                    image_mime = data.attachment.content_type
                prompt_for_ai = prompt or "صف هذه الصورة بالتفصيل."
            else:
                prompt_for_ai = f"{prompt}\n(المستخدم أرفق ملفًا باسم: {data.attachment.filename})"

        save_message(user_id, username, stored_content, target_bot)

        responses = {}

       
        requested_bots = [b.strip() for b in target_bot.split(",") if b.strip()]
        
        if "all" in requested_bots or not requested_bots:
            requested_bots = ["gemini", "mistral_small", "mistral_code", "mistral_vision"]

        tasks = {}
        if "gemini" in requested_bots:
            tasks["gemini"] = ask_gemini(prompt_for_ai, image_bytes=image_bytes, image_mime=image_mime)
        if "mistral_small" in requested_bots:
            tasks["mistral_small"] = ask_mistral_small(prompt_for_ai, image_bytes=image_bytes, image_mime=image_mime)
        if "mistral_code" in requested_bots:
            tasks["mistral_code"] = ask_mistral_code(prompt_for_ai, image_bytes=image_bytes, image_mime=image_mime)
        if "mistral_vision" in requested_bots:
            tasks["mistral_vision"] = ask_mistral_vision(prompt_for_ai, image_bytes=image_bytes, image_mime=image_mime)

        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        responses = {}
        display_names = {
            "gemini": "Gemini",
            "mistral_small": "ChatGpt",
            "mistral_code": "Code_ai",
            "mistral_vision": "photo_ai"
        }

        for bot_key, result in zip(tasks.keys(), results):
            bot_reply = str(result)
            responses[bot_key] = bot_reply
            friendly_name = display_names.get(bot_key, bot_key)
            save_message(user_id, friendly_name, bot_reply, target_bot)

            return {"responses": responses}

            
    except Exception as e:
        print(f"[/api/chat] Unexpected error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"خطأ داخلي غير متوقع: {type(e).__name__}: {e}")