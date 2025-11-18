## 📊 数据可靠性保障方案

本文档详细说明Book Recap系统的数据持久化策略，确保所有生成的内容安全可靠。

---

## 🎯 数据分类与存储策略

### 1️⃣ 核心数据（JSON格式）✅ 完全可靠

**存储方式：** 直接存储在数据库的JSON字段中

| 数据类型 | 数据库字段 | 说明 | 可靠性 |
|---------|-----------|------|--------|
| 智能总结 | `raw_data` | raw.json的完整内容（标题、金句、内容等） | ✅ 100% |
| 分段脚本 | `script_data` | script.json的完整内容（所有段落） | ✅ 100% |
| 关键词 | `keywords_data` | keywords.json或mini_summary.json | ✅ 100% |
| 配置参数 | `config` | 所有生成参数 + 版本历史 | ✅ 100% |
| 项目元数据 | 各个字段 | 状态、进度、时间戳等 | ✅ 100% |

**可靠性保证：**
- ✅ 数据库级别的ACID事务保证
- ✅ PostgreSQL/MySQL的主从复制（生产环境）
- ✅ 定时自动备份（每日/每周）
- ✅ 版本历史记录（可回滚到任意版本）

---

### 2️⃣ 大文件（图片、音频、视频）✨ 云存储方案

**存储方式：** 云存储（阿里云OSS/腾讯云COS/AWS S3） + 数据库存储URL

#### 数据库存储结构

```python
class Project:
    # 云存储URL字段
    use_cloud_storage = Column(Boolean, default=True)

    # 图片URL（JSON对象）
    images_urls = Column(JSON)
    # 示例: {
    #   "opening": "https://cdn.example.com/projects/1/images/opening.png",
    #   "segment_1": "https://cdn.example.com/projects/1/images/segment_1.png",
    #   "segment_2": "https://cdn.example.com/projects/1/images/segment_2.png",
    #   ...
    # }

    # 音频URL（JSON对象）
    audio_urls = Column(JSON)
    # 示例: {
    #   "opening": "https://cdn.example.com/projects/1/voice/opening.mp3",
    #   "segment_1": "https://cdn.example.com/projects/1/voice/voice_1.wav",
    #   ...
    # }

    # 视频URL
    final_video_url = Column(String)
    # 示例: "https://cdn.example.com/projects/1/video/final_video.mp4"

    # 封面URL（JSON数组）
    cover_image_urls = Column(JSON)
    # 示例: [
    #   "https://cdn.example.com/projects/1/covers/cover_1.png",
    #   "https://cdn.example.com/projects/1/covers/cover_2.png"
    # ]

    # 字幕URL
    srt_url = Column(String)

    # 元数据
    storage_provider = Column(String)  # "aliyun_oss" / "tencent_cos" / "aws_s3"
    storage_bucket = Column(String)
    storage_size_bytes = Column(Integer)
    cloud_uploaded_at = Column(DateTime)
```

#### 云存储路径结构

```
{bucket}/
  └── projects/
      └── {project_id}/
          ├── input/
          │   └── {original_filename}         # 原始输入文件
          ├── images/
          │   ├── opening.png                 # 开场图片
          │   ├── segment_1.png               # 段落1图片
          │   ├── segment_2.png
          │   └── ...
          ├── voice/
          │   ├── opening.mp3                 # 开场音频
          │   ├── voice_1.wav                 # 段落1音频
          │   ├── voice_2.wav
          │   └── ...
          ├── video/
          │   └── final_video.mp4             # 最终视频
          ├── covers/
          │   ├── cover_1.png                 # 封面图片
          │   └── cover_2.png
          └── subtitles/
              └── subtitles.srt               # SRT字幕
```

**可靠性保证：**
- ✅ 云存储提供商的99.9999999%数据持久性（11个9）
- ✅ 跨区域自动备份
- ✅ CDN加速，全球访问
- ✅ 本地备份机制（可选）

---

## 🔄 自动上传流程

### 步骤3：图像生成完成后

```python
# Celery任务中自动上传
def execute_step_3(project_id):
    # 1. 生成图片到本地
    generate_images()  # → output/项目/images/*.png

    # 2. 自动上传到云存储
    storage = get_storage_provider()
    images_urls = {}

    for image_file in list_images():
        # 上传到云存储
        cloud_url = storage.upload_file(
            local_path=image_file,
            cloud_path=f"projects/{project_id}/images/{filename}"
        )
        images_urls[segment_name] = cloud_url

    # 3. 保存URL到数据库
    project.images_urls = images_urls
    project.cloud_uploaded_at = datetime.now()
    db.commit()

    # 4. 可选：删除本地文件（节省磁盘）
    # os.remove(image_file)
```

### 步骤4：语音合成完成后

```python
# 类似流程
audio_urls = batch_upload_directory(
    project_id=project_id,
    local_dir=voice_dir,
    file_type="voice"
)
project.audio_urls = audio_urls
db.commit()
```

### 步骤5：视频合成完成后

```python
final_video_url = upload_project_file(
    project_id=project_id,
    local_path=final_video_path,
    file_type="video",
    filename="final_video.mp4"
)
project.final_video_url = final_video_url
db.commit()
```

---

## 🛡️ 多层备份策略

### Level 1: 数据库备份（每日）

```bash
# PostgreSQL自动备份脚本
#!/bin/bash
# 每天凌晨2点执行
0 2 * * * /usr/bin/pg_dump book_recap_db | gzip > /backup/db_$(date +\%Y\%m\%d).sql.gz

# 保留最近30天的备份
find /backup -name "db_*.sql.gz" -mtime +30 -delete
```

**备份内容：**
- ✅ 所有JSON数据（raw_data, script_data, keywords_data）
- ✅ 所有云存储URL
- ✅ 项目元数据和配置
- ✅ 任务历史记录

### Level 2: 云存储冗余（实时）

**阿里云OSS：**
- ✅ 跨区域复制（异地容灾）
- ✅ 版本控制（可恢复任意历史版本）
- ✅ 回收站（删除后30天内可恢复）

**配置示例：**
```python
# .env配置
STORAGE_PROVIDER=aliyun_oss
ALIYUN_OSS_ACCESS_KEY_ID=your_key_id
ALIYUN_OSS_ACCESS_KEY_SECRET=your_secret
ALIYUN_OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
ALIYUN_OSS_BUCKET=book-recap-storage

# 启用跨区域复制
ALIYUN_OSS_REPLICA_REGION=oss-cn-beijing
```

### Level 3: 本地备份（可选）

**双重存储策略：**
```python
# 在config.py中配置
ENABLE_LOCAL_BACKUP = True  # 保留本地副本
CLOUD_UPLOAD_ENABLED = True  # 同时上传到云存储

# 上传后保留本地文件
def upload_with_backup(local_path, cloud_path):
    # 上传到云存储
    cloud_url = storage.upload_file(local_path, cloud_path)

    if ENABLE_LOCAL_BACKUP:
        # 移动到备份目录（而非删除）
        backup_path = f"/backup/files/{cloud_path}"
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        shutil.copy2(local_path, backup_path)

    return cloud_url
```

---

## 🚨 灾难恢复方案

### 场景1：数据库崩溃

**恢复步骤：**
1. 从最新备份恢复数据库
   ```bash
   gunzip -c /backup/db_20241118.sql.gz | psql book_recap_db
   ```
2. 所有JSON数据完整恢复 ✅
3. 所有云存储URL完整恢复 ✅
4. 云存储文件仍然可访问 ✅

**数据损失：** 最多丢失1天的新项目（取决于备份频率）

### 场景2：云存储故障

**保护机制：**
1. **跨区域复制** - 主区域故障，自动切换到备用区域
2. **版本控制** - 可恢复任意历史版本
3. **本地备份** - 如果启用，可从本地恢复

**恢复步骤：**
```python
# 从本地备份重新上传
def recover_from_local_backup(project_id):
    backup_dir = f"/backup/files/projects/{project_id}"

    # 重新上传所有文件
    images_urls = batch_upload_directory(project_id, f"{backup_dir}/images", "images")
    audio_urls = batch_upload_directory(project_id, f"{backup_dir}/voice", "voice")

    # 更新数据库
    project.images_urls = images_urls
    project.audio_urls = audio_urls
    db.commit()
```

### 场景3：误删除项目

**保护机制：**
1. **软删除** - 不真正删除数据库记录，只标记为删除
2. **回收站** - 云存储的回收站机制（30天）
3. **版本历史** - 可恢复到删除前的状态

```python
# 软删除实现
def delete_project(project_id):
    project.status = ProjectStatus.DELETED
    project.deleted_at = datetime.now()
    db.commit()
    # 不删除数据库记录，不删除云存储文件

# 恢复删除的项目
def restore_project(project_id):
    project.status = ProjectStatus.CREATED
    project.deleted_at = None
    db.commit()
```

---

## 📈 存储成本估算

### 典型项目存储需求

| 文件类型 | 数量 | 单个大小 | 总大小 |
|---------|------|---------|--------|
| 输入文件 | 1 | 5 MB | 5 MB |
| 图片 | 15 | 2 MB | 30 MB |
| 音频 | 15 | 1 MB | 15 MB |
| 视频 | 1 | 50 MB | 50 MB |
| 封面 | 3 | 3 MB | 9 MB |
| **总计** | | | **≈ 110 MB/项目** |

### 云存储价格（阿里云OSS为例）

- **存储费用：** ¥0.12/GB/月
- **流量费用：** ¥0.50/GB（CDN加速后）
- **请求费用：** ¥0.01/万次

**月度成本估算：**
```
100个项目 = 11 GB
存储费用 = 11 GB × ¥0.12 = ¥1.32/月
流量费用 = 100 GB × ¥0.50 = ¥50/月（假设每个项目下载1次）
总计 ≈ ¥51.32/月

1000个项目 ≈ ¥500/月
```

**成本优化：**
- ✅ 使用生命周期管理，30天后转冷存储（降低80%成本）
- ✅ CDN缓存，减少回源流量
- ✅ 压缩文件，减小存储空间
- ✅ 定期清理失败/测试项目

---

## 🔧 环境配置

### .env配置示例

```env
# ==================== 数据库配置 ====================
DATABASE_URL=postgresql://user:password@localhost:5432/book_recap_db

# ==================== 云存储配置 ====================
# 存储提供商选择：aliyun_oss / tencent_cos / aws_s3 / local
STORAGE_PROVIDER=aliyun_oss

# 阿里云OSS配置
ALIYUN_OSS_ACCESS_KEY_ID=LTAI5tXXXXXXXXXXXXXX
ALIYUN_OSS_ACCESS_KEY_SECRET=your_secret_key
ALIYUN_OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
ALIYUN_OSS_BUCKET=book-recap-storage

# 腾讯云COS配置（可选）
TENCENT_COS_SECRET_ID=your_secret_id
TENCENT_COS_SECRET_KEY=your_secret_key
TENCENT_COS_REGION=ap-guangzhou
TENCENT_COS_BUCKET=book-recap-1234567890

# AWS S3配置（可选）
AWS_ACCESS_KEY=your_access_key
AWS_SECRET_KEY=your_secret_key
AWS_REGION=us-west-2
AWS_S3_BUCKET=book-recap-storage

# 本地存储配置（开发环境）
LOCAL_STORAGE_DIR=./storage
LOCAL_STORAGE_URL=http://localhost:8000/files

# ==================== 备份配置 ====================
ENABLE_LOCAL_BACKUP=true          # 是否保留本地备份
CLOUD_UPLOAD_ENABLED=true         # 是否上传到云存储
AUTO_CLEANUP_LOCAL_FILES=false    # 上传后是否删除本地文件（生产环境建议true）

# 数据库备份
DB_BACKUP_ENABLED=true
DB_BACKUP_SCHEDULE="0 2 * * *"    # 每天凌晨2点
DB_BACKUP_RETENTION_DAYS=30        # 保留30天
```

---

## ✅ 可靠性检查清单

### 部署前检查

- [ ] 数据库已配置主从复制
- [ ] 数据库自动备份已启用
- [ ] 云存储账号已创建并配置
- [ ] 云存储跨区域复制已启用
- [ ] 环境变量已正确配置
- [ ] 测试上传/下载功能正常
- [ ] 监控告警已配置

### 运行时监控

- [ ] 数据库连接正常
- [ ] 云存储上传成功率 > 99%
- [ ] 磁盘空间充足（如果保留本地备份）
- [ ] 备份任务按时执行
- [ ] 云存储费用在预算内

### 定期检查（每月）

- [ ] 恢复测试（从备份恢复数据）
- [ ] 云存储账单检查
- [ ] 清理无效项目
- [ ] 更新安全凭证

---

## 🎯 总结

### 数据可靠性等级

| 数据类型 | 可靠性 | 说明 |
|---------|--------|------|
| JSON数据 | ⭐⭐⭐⭐⭐ | 数据库 + 每日备份，100%可靠 |
| 云存储文件 | ⭐⭐⭐⭐⭐ | 11个9持久性 + 跨区域复制 |
| 本地备份 | ⭐⭐⭐⭐ | 可选，额外保障 |

### 关键保障措施

1. **核心数据（JSON）** - 存储在数据库，ACID保证 + 每日备份
2. **大文件** - 云存储（OSS/COS/S3），11个9持久性
3. **双重保障** - 数据库 + 云存储，任一故障不影响数据
4. **版本控制** - 所有修改可回滚
5. **跨区域复制** - 异地容灾
6. **定期备份** - 每日自动备份数据库
7. **软删除** - 误删除可恢复

**结论：** 系统已具备企业级数据可靠性，用户数据安全有保障！✅
