"""
FastAPI主应用
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import os
from contextlib import asynccontextmanager

from backend.database import init_db
from backend.api import projects, tasks, websocket, editor, media_versions


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    init_db()
    print("✅ 数据库初始化完成")

    # 确保必要目录存在
    os.makedirs("output", exist_ok=True)
    os.makedirs("input", exist_ok=True)
    os.makedirs("music", exist_ok=True)
    print("✅ 目录结构检查完成")

    yield

    # 关闭时清理资源
    print("🛑 应用关闭")


# 创建FastAPI应用
app = FastAPI(
    title="Book Recap Video Generator API",
    description="智能书籍内容转视频系统 - Web API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(websocket.router)
app.include_router(editor.router)
app.include_router(media_versions.router)


# 静态文件服务（用于提供生成的图片、音频、视频）
@app.get("/api/files/{project_id}/images/{filename}")
async def serve_image(project_id: int, filename: str):
    """提供图片文件"""
    from backend.database import SessionLocal
    from backend.models import Project

    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return JSONResponse(status_code=404, content={"detail": "Project not found"})

        file_path = os.path.join(project.project_dir, "images", filename)
        if not os.path.exists(file_path):
            return JSONResponse(status_code=404, content={"detail": "File not found"})

        return FileResponse(file_path)
    finally:
        db.close()


@app.get("/api/files/{project_id}/audio/{filename}")
async def serve_audio(project_id: int, filename: str):
    """提供音频文件"""
    from backend.database import SessionLocal
    from backend.models import Project

    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return JSONResponse(status_code=404, content={"detail": "Project not found"})

        file_path = os.path.join(project.project_dir, "voice", filename)
        if not os.path.exists(file_path):
            return JSONResponse(status_code=404, content={"detail": "File not found"})

        return FileResponse(file_path)
    finally:
        db.close()


@app.get("/api/files/{project_id}/video")
async def serve_video(project_id: int):
    """提供视频文件"""
    from backend.database import SessionLocal
    from backend.models import Project

    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return JSONResponse(status_code=404, content={"detail": "Project not found"})

        if not project.final_video_path or not os.path.exists(project.final_video_path):
            return JSONResponse(status_code=404, content={"detail": "Video not found"})

        return FileResponse(project.final_video_path)
    finally:
        db.close()


@app.get("/api/files/{project_id}/cover/{filename}")
async def serve_cover(project_id: int, filename: str):
    """提供封面图片"""
    from backend.database import SessionLocal
    from backend.models import Project

    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return JSONResponse(status_code=404, content={"detail": "Project not found"})

        file_path = os.path.join(project.project_dir, filename)
        if not os.path.exists(file_path):
            return JSONResponse(status_code=404, content={"detail": "File not found"})

        return FileResponse(file_path)
    finally:
        db.close()


# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "book-recap-api"}


# 根路径
@app.get("/")
async def root():
    """API根路径"""
    return {
        "message": "Book Recap Video Generator API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


# 异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    import traceback
    error_detail = str(exc)
    error_traceback = traceback.format_exc()

    print(f"❌ Error: {error_detail}")
    print(error_traceback)

    return JSONResponse(
        status_code=500,
        content={
            "detail": error_detail,
            "type": type(exc).__name__
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
