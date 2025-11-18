"""
数据库迁移脚本：添加云存储支持字段

使用方法：
    python -m backend.migrate_add_cloud_storage
"""
import os
import sys
from sqlalchemy import text

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine, SessionLocal
from backend.models import Project


def migrate_database():
    """执行数据库迁移"""
    print("开始数据库迁移：添加云存储支持字段...")

    db = SessionLocal()

    try:
        # 检查表是否存在
        result = db.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='projects'"
        ))
        if not result.fetchone():
            print("❌ projects表不存在，请先运行主程序初始化数据库")
            return

        # SQLite ALTER TABLE 只支持添加列，不支持修改列
        # 所以我们一次添加一个列
        columns_to_add = [
            ("use_cloud_storage", "BOOLEAN DEFAULT 1"),
            ("input_file_url", "VARCHAR(2000)"),
            ("images_urls", "JSON"),
            ("audio_urls", "JSON"),
            ("final_video_url", "VARCHAR(2000)"),
            ("cover_image_urls", "JSON"),
            ("srt_url", "VARCHAR(2000)"),
            ("storage_provider", "VARCHAR(50)"),
            ("storage_bucket", "VARCHAR(200)"),
            ("storage_size_bytes", "INTEGER DEFAULT 0"),
            ("cloud_uploaded_at", "DATETIME"),
        ]

        for column_name, column_type in columns_to_add:
            try:
                # 检查列是否已存在
                result = db.execute(text(f"PRAGMA table_info(projects)"))
                columns = [row[1] for row in result.fetchall()]

                if column_name not in columns:
                    # 添加新列
                    db.execute(text(
                        f"ALTER TABLE projects ADD COLUMN {column_name} {column_type}"
                    ))
                    db.commit()
                    print(f"✅ 添加字段: {column_name}")
                else:
                    print(f"⏭️  字段已存在: {column_name}")

            except Exception as e:
                print(f"⚠️  添加字段 {column_name} 时出错: {str(e)}")
                db.rollback()

        print("\n✨ 数据库迁移完成！")
        print("\n📝 后续步骤：")
        print("1. 在 .env 文件中配置云存储提供商")
        print("2. 设置相应的认证信息（AccessKey等）")
        print("3. 重启后端服务")

    except Exception as e:
        print(f"❌ 迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    migrate_database()
