import { useState, useEffect } from 'react';
import {
  Card,
  Image,
  Space,
  Button,
  Upload,
  Modal,
  Input,
  message,
  Row,
  Col,
  Badge,
  Tag,
  Timeline,
  Tooltip,
} from 'antd';
import {
  ReloadOutlined,
  UploadOutlined,
  EyeOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  DeleteOutlined,
  HistoryOutlined,
} from '@ant-design/icons';
import type { UploadFile } from 'antd';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

interface ImageVersion {
  id: number;
  version: number;
  is_active: boolean;
  cloud_url?: string;
  local_path?: string;
  generation_method: string;
  generation_params?: any;
  file_size_bytes: number;
  width?: number;
  height?: number;
  created_at: string;
  created_by: string;
  note?: string;
}

interface ImageVersionGroup {
  filename: string;
  media_type: string;
  segment_index?: number;
  versions: ImageVersion[];
  active_version?: number;
}

interface ImageVersionManagerProps {
  projectId: number;
  segmentCount: number;
  hasOpeningQuote?: boolean;
}

function ImageVersionManager({
  projectId,
  segmentCount,
  hasOpeningQuote = false,
}: ImageVersionManagerProps) {
  const [imagesData, setImagesData] = useState<Record<string, ImageVersionGroup>>({});
  const [loading, setLoading] = useState(false);
  const [regenerateModal, setRegenerateModal] = useState(false);
  const [historyModal, setHistoryModal] = useState(false);
  const [selectedFilename, setSelectedFilename] = useState<string | null>(null);
  const [customPrompt, setCustomPrompt] = useState('');
  const [uploading, setUploading] = useState(false);

  // 加载所有图片版本数据
  const loadAllVersions = async () => {
    setLoading(true);
    try {
      const response = await axios.get(
        `${API_BASE_URL}/media-versions/projects/${projectId}/all-versions?media_type=image`
      );

      const grouped: Record<string, ImageVersionGroup> = {};
      response.data.media.forEach((item: ImageVersionGroup) => {
        grouped[item.filename] = item;
      });

      setImagesData(grouped);
    } catch (error: any) {
      message.error('加载图片版本失败：' + error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllVersions();
  }, [projectId]);

  // 打开历史版本对话框
  const handleOpenHistory = (filename: string) => {
    setSelectedFilename(filename);
    setHistoryModal(true);
  };

  // 设置活跃版本
  const handleSetActiveVersion = async (filename: string, version: number) => {
    try {
      await axios.post(
        `${API_BASE_URL}/media-versions/projects/${projectId}/images/${filename}/set-active`,
        null,
        { params: { version } }
      );
      message.success(`已将版本 ${version} 设为活跃版本`);
      loadAllVersions();
      setHistoryModal(false);
    } catch (error: any) {
      message.error('设置活跃版本失败：' + error.message);
    }
  };

  // 上传新版本
  const handleUploadNewVersion = async (file: File, filename: string, note?: string) => {
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      if (note) {
        formData.append('note', note);
      }

      await axios.post(
        `${API_BASE_URL}/media-versions/projects/${projectId}/images/${filename}/upload`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
        }
      );

      message.success('新版本上传成功！');
      loadAllVersions();
    } catch (error: any) {
      message.error('上传失败：' + error.message);
    } finally {
      setUploading(false);
    }
    return false; // 阻止自动上传
  };

  // 删除版本
  const handleDeleteVersion = async (versionId: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个版本吗？此操作不可撤销。',
      onOk: async () => {
        try {
          await axios.delete(`${API_BASE_URL}/media-versions/versions/${versionId}`);
          message.success('版本已删除');
          loadAllVersions();
        } catch (error: any) {
          message.error('删除失败：' + error.message);
        }
      },
    });
  };

  // 获取活跃版本的URL
  const getActiveVersionUrl = (filename: string): string => {
    const imageGroup = imagesData[filename];
    if (!imageGroup || !imageGroup.active_version) {
      return `${API_BASE_URL}/files/${projectId}/images/${filename}`;
    }

    const activeVersion = imageGroup.versions.find(
      v => v.version === imageGroup.active_version
    );

    return activeVersion?.cloud_url || activeVersion?.local_path || '';
  };

  // 渲染版本历史对话框
  const renderHistoryModal = () => {
    if (!selectedFilename || !imagesData[selectedFilename]) {
      return null;
    }

    const imageGroup = imagesData[selectedFilename];

    return (
      <Modal
        title={
          <Space>
            <HistoryOutlined />
            版本历史 - {selectedFilename}
          </Space>
        }
        open={historyModal}
        onCancel={() => setHistoryModal(false)}
        footer={null}
        width={900}
      >
        <Timeline>
          {imageGroup.versions.map((version) => (
            <Timeline.Item
              key={version.id}
              dot={
                version.is_active ? (
                  <CheckCircleOutlined style={{ fontSize: 16, color: '#52c41a' }} />
                ) : (
                  <ClockCircleOutlined style={{ fontSize: 16 }} />
                )
              }
              color={version.is_active ? 'green' : 'gray'}
            >
              <Card
                size="small"
                title={
                  <Space>
                    <span>版本 {version.version}</span>
                    {version.is_active && (
                      <Tag color="success">活跃</Tag>
                    )}
                    <Tag color={version.generation_method === 'ai_generated' ? 'blue' : 'orange'}>
                      {version.generation_method === 'ai_generated' ? 'AI生成' : '用户上传'}
                    </Tag>
                  </Space>
                }
                extra={
                  !version.is_active && (
                    <Space>
                      <Button
                        size="small"
                        type="primary"
                        onClick={() => handleSetActiveVersion(selectedFilename, version.version)}
                      >
                        设为活跃
                      </Button>
                      <Button
                        size="small"
                        danger
                        icon={<DeleteOutlined />}
                        onClick={() => handleDeleteVersion(version.id)}
                      >
                        删除
                      </Button>
                    </Space>
                  )
                }
              >
                <Row gutter={16}>
                  <Col span={12}>
                    <Image
                      src={version.cloud_url || version.local_path}
                      alt={`Version ${version.version}`}
                      style={{ width: '100%', maxHeight: 300, objectFit: 'cover' }}
                    />
                  </Col>
                  <Col span={12}>
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <div>
                        <strong>创建时间：</strong>
                        {new Date(version.created_at).toLocaleString('zh-CN')}
                      </div>
                      <div>
                        <strong>创建者：</strong>
                        {version.created_by}
                      </div>
                      {version.width && version.height && (
                        <div>
                          <strong>尺寸：</strong>
                          {version.width} × {version.height}
                        </div>
                      )}
                      <div>
                        <strong>文件大小：</strong>
                        {(version.file_size_bytes / 1024).toFixed(2)} KB
                      </div>
                      {version.generation_params?.prompt && (
                        <div>
                          <strong>生成提示词：</strong>
                          {version.generation_params.prompt}
                        </div>
                      )}
                      {version.note && (
                        <div>
                          <strong>备注：</strong>
                          {version.note}
                        </div>
                      )}
                    </Space>
                  </Col>
                </Row>
              </Card>
            </Timeline.Item>
          ))}
        </Timeline>
      </Modal>
    );
  };

  // 渲染图片卡片
  const renderImageCard = (filename: string, title: string) => {
    const imageGroup = imagesData[filename];
    const hasVersions = imageGroup && imageGroup.versions.length > 0;
    const versionCount = imageGroup?.versions.length || 0;
    const activeUrl = getActiveVersionUrl(filename);

    return (
      <Col xs={12} sm={8} md={6} lg={4} key={filename}>
        <Badge count={versionCount} offset={[-10, 10]}>
          <Card
            size="small"
            title={title}
            cover={
              <Image
                src={activeUrl}
                alt={title}
                style={{ width: '100%', height: 200, objectFit: 'cover' }}
                fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
              />
            }
            actions={[
              <Tooltip title="查看历史版本">
                <Button
                  size="small"
                  icon={<HistoryOutlined />}
                  onClick={() => handleOpenHistory(filename)}
                  disabled={!hasVersions}
                >
                  历史 ({versionCount})
                </Button>
              </Tooltip>,
              <Upload
                showUploadList={false}
                beforeUpload={(file) => handleUploadNewVersion(file, filename)}
                accept="image/*"
              >
                <Button size="small" icon={<UploadOutlined />} loading={uploading}>
                  上传新版本
                </Button>
              </Upload>,
            ]}
          >
            {hasVersions && imageGroup.active_version && (
              <div style={{ textAlign: 'center', color: '#999', fontSize: 12 }}>
                当前版本: v{imageGroup.active_version}
              </div>
            )}
          </Card>
        </Badge>
      </Col>
    );
  };

  return (
    <div>
      <Card
        title="图片版本管理"
        extra={
          <Button icon={<ReloadOutlined />} onClick={loadAllVersions} loading={loading}>
            刷新
          </Button>
        }
      >
        <div style={{ marginBottom: 16, color: '#666' }}>
          💡 每个图片可以有多个版本，上传或重新生成会创建新版本，选择一个版本作为活跃版本用于视频合成。
        </div>

        <Row gutter={[16, 16]}>
          {/* 开场图片 */}
          {hasOpeningQuote && renderImageCard('opening.png', '开场图片')}

          {/* 段落图片 */}
          {Array.from({ length: segmentCount }, (_, i) => i + 1).map((segmentIndex) => {
            const filename = `segment_${segmentIndex}.png`;
            return renderImageCard(filename, `段落 ${segmentIndex}`);
          })}
        </Row>
      </Card>

      {/* 版本历史对话框 */}
      {renderHistoryModal()}
    </div>
  );
}

export default ImageVersionManager;
