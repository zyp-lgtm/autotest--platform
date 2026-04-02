from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import get_settings

settings = get_settings()

app = FastAPI(title="测试自动化平台", version="0.1.0")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "测试自动化平台 API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}