"""
云存储服务抽象层
支持多种云存储提供商：阿里云OSS、AWS S3、腾讯云COS等
"""
from abc import ABC, abstractmethod
from typing import Optional, BinaryIO
import os
from datetime import datetime
import mimetypes


class CloudStorageProvider(ABC):
    """云存储提供商抽象基类"""

    @abstractmethod
    def upload_file(self, local_path: str, cloud_path: str) -> str:
        """
        上传文件到云存储

        Args:
            local_path: 本地文件路径
            cloud_path: 云存储路径（相对路径，如 projects/1/images/segment_1.png）

        Returns:
            完整的云存储URL
        """
        pass

    @abstractmethod
    def upload_bytes(self, data: bytes, cloud_path: str, content_type: str = None) -> str:
        """
        上传二进制数据到云存储

        Args:
            data: 二进制数据
            cloud_path: 云存储路径
            content_type: MIME类型（如 image/png）

        Returns:
            完整的云存储URL
        """
        pass

    @abstractmethod
    def download_file(self, cloud_path: str, local_path: str) -> None:
        """
        从云存储下载文件到本地

        Args:
            cloud_path: 云存储路径
            local_path: 本地保存路径
        """
        pass

    @abstractmethod
    def delete_file(self, cloud_path: str) -> None:
        """
        删除云存储中的文件

        Args:
            cloud_path: 云存储路径
        """
        pass

    @abstractmethod
    def get_public_url(self, cloud_path: str) -> str:
        """
        获取文件的公开访问URL

        Args:
            cloud_path: 云存储路径

        Returns:
            公开访问URL
        """
        pass

    @abstractmethod
    def file_exists(self, cloud_path: str) -> bool:
        """
        检查文件是否存在

        Args:
            cloud_path: 云存储路径

        Returns:
            是否存在
        """
        pass


class AlibabaOSSProvider(CloudStorageProvider):
    """阿里云OSS存储提供商"""

    def __init__(self, access_key_id: str, access_key_secret: str,
                 endpoint: str, bucket_name: str):
        """
        初始化阿里云OSS客户端

        Args:
            access_key_id: AccessKey ID
            access_key_secret: AccessKey Secret
            endpoint: OSS Endpoint（如 oss-cn-hangzhou.aliyuncs.com）
            bucket_name: Bucket名称
        """
        try:
            import oss2
            self.auth = oss2.Auth(access_key_id, access_key_secret)
            self.bucket = oss2.Bucket(self.auth, endpoint, bucket_name)
            self.bucket_name = bucket_name
            self.endpoint = endpoint
        except ImportError:
            raise ImportError("请安装阿里云OSS SDK: pip install oss2")

    def upload_file(self, local_path: str, cloud_path: str) -> str:
        """上传文件"""
        self.bucket.put_object_from_file(cloud_path, local_path)
        return self.get_public_url(cloud_path)

    def upload_bytes(self, data: bytes, cloud_path: str, content_type: str = None) -> str:
        """上传二进制数据"""
        headers = {}
        if content_type:
            headers['Content-Type'] = content_type
        self.bucket.put_object(cloud_path, data, headers=headers)
        return self.get_public_url(cloud_path)

    def download_file(self, cloud_path: str, local_path: str) -> None:
        """下载文件"""
        self.bucket.get_object_to_file(cloud_path, local_path)

    def delete_file(self, cloud_path: str) -> None:
        """删除文件"""
        self.bucket.delete_object(cloud_path)

    def get_public_url(self, cloud_path: str) -> str:
        """获取公开URL"""
        # 如果bucket是公共读，直接返回URL
        # 如果是私有bucket，需要生成签名URL
        return f"https://{self.bucket_name}.{self.endpoint}/{cloud_path}"

    def file_exists(self, cloud_path: str) -> bool:
        """检查文件是否存在"""
        return self.bucket.object_exists(cloud_path)


class TencentCOSProvider(CloudStorageProvider):
    """腾讯云COS存储提供商"""

    def __init__(self, secret_id: str, secret_key: str,
                 region: str, bucket_name: str):
        """
        初始化腾讯云COS客户端

        Args:
            secret_id: SecretId
            secret_key: SecretKey
            region: 地域（如 ap-guangzhou）
            bucket_name: Bucket名称（如 mybucket-1250000000）
        """
        try:
            from qcloud_cos import CosConfig, CosS3Client
            config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
            self.client = CosS3Client(config)
            self.bucket_name = bucket_name
            self.region = region
        except ImportError:
            raise ImportError("请安装腾讯云COS SDK: pip install cos-python-sdk-v5")

    def upload_file(self, local_path: str, cloud_path: str) -> str:
        """上传文件"""
        with open(local_path, 'rb') as f:
            self.client.put_object(
                Bucket=self.bucket_name,
                Body=f,
                Key=cloud_path,
            )
        return self.get_public_url(cloud_path)

    def upload_bytes(self, data: bytes, cloud_path: str, content_type: str = None) -> str:
        """上传二进制数据"""
        self.client.put_object(
            Bucket=self.bucket_name,
            Body=data,
            Key=cloud_path,
            ContentType=content_type
        )
        return self.get_public_url(cloud_path)

    def download_file(self, cloud_path: str, local_path: str) -> None:
        """下载文件"""
        response = self.client.get_object(
            Bucket=self.bucket_name,
            Key=cloud_path
        )
        with open(local_path, 'wb') as f:
            f.write(response['Body'].read())

    def delete_file(self, cloud_path: str) -> None:
        """删除文件"""
        self.client.delete_object(
            Bucket=self.bucket_name,
            Key=cloud_path
        )

    def get_public_url(self, cloud_path: str) -> str:
        """获取公开URL"""
        return f"https://{self.bucket_name}.cos.{self.region}.myqcloud.com/{cloud_path}"

    def file_exists(self, cloud_path: str) -> bool:
        """检查文件是否存在"""
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=cloud_path)
            return True
        except:
            return False


class AWSS3Provider(CloudStorageProvider):
    """AWS S3存储提供商"""

    def __init__(self, access_key: str, secret_key: str,
                 region: str, bucket_name: str):
        """
        初始化AWS S3客户端

        Args:
            access_key: AWS Access Key
            secret_key: AWS Secret Key
            region: AWS区域（如 us-west-2）
            bucket_name: S3 Bucket名称
        """
        try:
            import boto3
            self.client = boto3.client(
                's3',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
            self.bucket_name = bucket_name
            self.region = region
        except ImportError:
            raise ImportError("请安装AWS SDK: pip install boto3")

    def upload_file(self, local_path: str, cloud_path: str) -> str:
        """上传文件"""
        self.client.upload_file(local_path, self.bucket_name, cloud_path)
        return self.get_public_url(cloud_path)

    def upload_bytes(self, data: bytes, cloud_path: str, content_type: str = None) -> str:
        """上传二进制数据"""
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=cloud_path,
            Body=data,
            **extra_args
        )
        return self.get_public_url(cloud_path)

    def download_file(self, cloud_path: str, local_path: str) -> None:
        """下载文件"""
        self.client.download_file(self.bucket_name, cloud_path, local_path)

    def delete_file(self, cloud_path: str) -> None:
        """删除文件"""
        self.client.delete_object(Bucket=self.bucket_name, Key=cloud_path)

    def get_public_url(self, cloud_path: str) -> str:
        """获取公开URL"""
        return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{cloud_path}"

    def file_exists(self, cloud_path: str) -> bool:
        """检查文件是否存在"""
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=cloud_path)
            return True
        except:
            return False


class LocalStorageProvider(CloudStorageProvider):
    """本地存储提供商（用于开发/测试）"""

    def __init__(self, base_dir: str, base_url: str = None):
        """
        初始化本地存储

        Args:
            base_dir: 本地存储根目录
            base_url: 访问URL前缀（如 http://localhost:8000/files）
        """
        self.base_dir = os.path.abspath(base_dir)
        self.base_url = base_url or "http://localhost:8000/files"
        os.makedirs(self.base_dir, exist_ok=True)

    def upload_file(self, local_path: str, cloud_path: str) -> str:
        """复制文件到存储目录"""
        target_path = os.path.join(self.base_dir, cloud_path)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        import shutil
        shutil.copy2(local_path, target_path)

        return self.get_public_url(cloud_path)

    def upload_bytes(self, data: bytes, cloud_path: str, content_type: str = None) -> str:
        """写入二进制数据"""
        target_path = os.path.join(self.base_dir, cloud_path)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        with open(target_path, 'wb') as f:
            f.write(data)

        return self.get_public_url(cloud_path)

    def download_file(self, cloud_path: str, local_path: str) -> None:
        """复制文件到本地"""
        source_path = os.path.join(self.base_dir, cloud_path)
        import shutil
        shutil.copy2(source_path, local_path)

    def delete_file(self, cloud_path: str) -> None:
        """删除文件"""
        target_path = os.path.join(self.base_dir, cloud_path)
        if os.path.exists(target_path):
            os.remove(target_path)

    def get_public_url(self, cloud_path: str) -> str:
        """获取访问URL"""
        return f"{self.base_url}/{cloud_path}"

    def file_exists(self, cloud_path: str) -> bool:
        """检查文件是否存在"""
        return os.path.exists(os.path.join(self.base_dir, cloud_path))


# ==================== 工厂函数 ====================

def get_storage_provider() -> CloudStorageProvider:
    """
    根据环境变量获取云存储提供商

    环境变量配置：
    - STORAGE_PROVIDER: 提供商类型（aliyun_oss/tencent_cos/aws_s3/local）
    - 各提供商的认证信息

    Returns:
        CloudStorageProvider实例
    """
    provider_type = os.getenv("STORAGE_PROVIDER", "local").lower()

    if provider_type == "aliyun_oss":
        return AlibabaOSSProvider(
            access_key_id=os.getenv("ALIYUN_OSS_ACCESS_KEY_ID"),
            access_key_secret=os.getenv("ALIYUN_OSS_ACCESS_KEY_SECRET"),
            endpoint=os.getenv("ALIYUN_OSS_ENDPOINT"),
            bucket_name=os.getenv("ALIYUN_OSS_BUCKET")
        )

    elif provider_type == "tencent_cos":
        return TencentCOSProvider(
            secret_id=os.getenv("TENCENT_COS_SECRET_ID"),
            secret_key=os.getenv("TENCENT_COS_SECRET_KEY"),
            region=os.getenv("TENCENT_COS_REGION"),
            bucket_name=os.getenv("TENCENT_COS_BUCKET")
        )

    elif provider_type == "aws_s3":
        return AWSS3Provider(
            access_key=os.getenv("AWS_ACCESS_KEY"),
            secret_key=os.getenv("AWS_SECRET_KEY"),
            region=os.getenv("AWS_REGION"),
            bucket_name=os.getenv("AWS_S3_BUCKET")
        )

    else:  # local
        return LocalStorageProvider(
            base_dir=os.getenv("LOCAL_STORAGE_DIR", "./storage"),
            base_url=os.getenv("LOCAL_STORAGE_URL", "http://localhost:8000/files")
        )


# ==================== 辅助函数 ====================

def upload_project_file(project_id: int, local_path: str,
                       file_type: str, filename: str = None) -> str:
    """
    上传项目文件到云存储

    Args:
        project_id: 项目ID
        local_path: 本地文件路径
        file_type: 文件类型（input/images/voice/video/cover）
        filename: 文件名（不提供则从local_path提取）

    Returns:
        云存储URL
    """
    storage = get_storage_provider()

    if filename is None:
        filename = os.path.basename(local_path)

    # 构建云存储路径：projects/{project_id}/{file_type}/{filename}
    cloud_path = f"projects/{project_id}/{file_type}/{filename}"

    return storage.upload_file(local_path, cloud_path)


def batch_upload_directory(project_id: int, local_dir: str,
                           file_type: str) -> dict:
    """
    批量上传目录中的所有文件

    Args:
        project_id: 项目ID
        local_dir: 本地目录路径
        file_type: 文件类型

    Returns:
        文件名 -> 云存储URL的映射
    """
    storage = get_storage_provider()
    results = {}

    if not os.path.exists(local_dir):
        return results

    for filename in os.listdir(local_dir):
        local_path = os.path.join(local_dir, filename)
        if os.path.isfile(local_path):
            cloud_path = f"projects/{project_id}/{file_type}/{filename}"
            url = storage.upload_file(local_path, cloud_path)
            results[filename] = url

    return results
