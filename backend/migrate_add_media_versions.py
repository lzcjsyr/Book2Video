"""
数据库迁移脚本：添加媒体版本管理表

使用方法：
    python -m backend.migrate_add_media_versions
"""
import os
import sys
from sqlalchemy import text

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine, SessionLocal, Base
from backend.models import MediaVersion


def migrate_database():
    """执行数据库迁移"""
    print("开始数据库迁移：添加媒体版本管理表...")

    try:
        # 创建所有表（如果不存在）
        Base.metadata.create_all(bind=engine)

        print("✅ media_versions 表创建成功")
        print("\n📝 表结构：")
        print("- id: 主键")
        print("- project_id: 关联项目ID")
        print("- media_type: 媒体类型（image/audio）")
        print("- filename: 文件名")
        print("- segment_index: 段落索引")
        print("- version: 版本号")
        print("- is_active: 是否为活跃版本")
        print("- local_path: 本地路径")
        print("- cloud_url: 云存储URL")
        print("- generation_method: 生成方式")
        print("- generation_params: 生成参数（JSON）")
        print("- file_size_bytes: 文件大小")
        print("- duration_seconds: 音频时长")
        print("- width: 图片宽度")
        print("- height: 图片高度")
        print("- created_at: 创建时间")
        print("- created_by: 创建者")
        print("- note: 备注")

        print("\n✨ 数据库迁移完成！")
        print("\n📝 后续步骤：")
        print("1. 重启后端服务")
        print("2. 访问 /docs 查看新的API端点")
        print("3. 在前端使用 ImageVersionManager 和 AudioVersionManager 组件")

    except Exception as e:
        print(f"❌ 迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    migrate_database()
