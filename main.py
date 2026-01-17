from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router 
import uvicorn

app = FastAPI()

# تفعيل الـ CORS عشان الـ Frontend يقدر يكلم الـ API من سيرفرات مختلفة
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # دي بتسمح لأي موقع يكلم السيرفر، وممكن نخصصها بعدين
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 
    # ملحوظة: خليتها 0.0.0.0 عشان المواقع اللي هنرفع عليها بتطلب كدة