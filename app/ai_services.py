import os
import re
import base64
import httpx
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

GEMINI_KEY = os.getenv("gemini_key")
mistral_key = os.getenv("MISTRAL_KEY")


GEMINI_CLIENT = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None

GEMINI_MODEL_CANDIDATES = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-flash-latest",
]



mistral_URL="https://api.mistral.ai/v1/chat/completions"
mistral_MODEL_SMALL="mistral-small-latest"
mistral_MODEL_CODE="codestral-latest"
mistral_MODEL_VISION="pixtral-12b-2409"

PLAIN_TEXT_INSTRUCTION = (
    "أجب بنص عادي واضح فقط. ممنوع استخدام أي رموز تنسيق مثل ** أو __ أو "
    "# أو ``` أو النجوم كنقاط. لو احتجت تعداد نقاط، استخدم أرقام عادية "
    "(1. 2. 3.) أو اسطر منفصلة بدون أي رمز قبلها."
)


def strip_markdown(text: str) -> str:
    """طبقة حماية إضافية: تشيل أي رموز ماركداون لو النموذج تجاهل التعليمات،
    عشان الرد يوصل نظيف حتى لو الواجهة الأمامية بتعرضه كنص عادي فقط."""
    if not text:
        return text
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"__(.*?)__", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"\1", text)
    text = re.sub(r"`{1,3}([^`]*?)`{1,3}", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*+]\s+", "- ", text, flags=re.MULTILINE)
    return text.strip()


def _to_b64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


async def ask_gemini(
    prompt: str,
    history: str = "",
    image_bytes: bytes | None = None,
    image_mime: str | None = None,
) -> str:
    if not GEMINI_CLIENT:
        return "خطأ في Gemini: gemini_key غير موجود أو فاضي في ملف .env"

    user_text = f"{history}\n\n{prompt}" if history else prompt
    contents = [user_text]
    if image_bytes and image_mime:
        contents.append(types.Part.from_bytes(data=image_bytes, mime_type=image_mime))

    config = types.GenerateContentConfig(system_instruction=PLAIN_TEXT_INSTRUCTION)

    last_error = None
    for model_name in GEMINI_MODEL_CANDIDATES:
        try:
            response = await GEMINI_CLIENT.aio.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
            return strip_markdown(response.text)
        except Exception as e:
            last_error = e
            continue
    return f"خطأ في Gemini: {last_error}"


    
async def _ask_mistral_api(
        model_id:str,
        prompt:str,
        provider_label : str,
        history: str="",
        image_bytes: bytes | None=None,
        image_mime: str|None=None,
)-> str:
    if not mistral_key:
        return "error"
    user_text=f"{history}\n\n{prompt}"if history else prompt
    if image_bytes and image_mime:
        user_content=[{"type":"text","text":user_text},
                      {"type":"image_url","image_url":{"url":f"data:{image_mime};base64,{_to_b64(image_bytes)}"}}]
    else:
        user_content=user_text
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response=await client.post(
            url=mistral_URL,
            headers={
                "authorization":f"Bearer {mistral_key}",
                "content-type":"application/json"},
                 json={"model":model_id,
                        "messages":[
                            {"role":"system",
                             "content":PLAIN_TEXT_INSTRUCTION},
                             {"role":"user",
                              "content":user_content}
                              ]})
            if response.status_code==401 or response.status_code==403:
                return "status error" 
            
            data=response.json()
            if "choices" in data:
                return strip_markdown(data["choices"][0]["message"]["content"])
            else:
                return f"{provider_label}:{data}"
    except Exception as e:
        return f"{provider_label}:{str(e)}"
async def ask_mistral_vision(
        
        prompt:str,
        history: str="",
        image_bytes: bytes | None=None,
        image_mime: str|None=None,)-> str:
    return await _ask_mistral_api(
        mistral_MODEL_VISION,
        prompt,
        "mistral vision",
        history,
        image_bytes,
        image_mime

    )
async def ask_mistral_small(
        prompt:str,
        history: str="",
        image_bytes: bytes | None=None,
        image_mime: str|None=None,)-> str:
    return await _ask_mistral_api(mistral_MODEL_SMALL,prompt,
                                  "Mistral Small",history,image_bytes,image_mime)
async def ask_mistral_code(
        prompt:str,
        history: str="",
        image_bytes: bytes | None=None,
        image_mime: str|None=None,)-> str:
    return await _ask_mistral_api(mistral_MODEL_CODE,prompt,
                                      "Codestral",history,image_bytes,image_mime)