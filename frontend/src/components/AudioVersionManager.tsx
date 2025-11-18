import { useState, useEffect, useRef } from 'react';
import {
  Card,
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
  Slider,
} from 'antd';
import {
  ReloadOutlined,
  UploadOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  DeleteOutlined,
  HistoryOutlined,
  SoundOutlined,
} from '@ant-design/icons';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

interface AudioVersion {
  id: number;
  version: number;
  is_active: boolean;
  cloud_url?: string;
  local_path?: string;
  generation_method: string;
  generation_params?: any;
  file_size_bytes: number;
  duration_seconds?: number;
  created_at: string;
  created_by: string;
  note?: string;
}

interface AudioVersionGroup {
  filename: string;
  media_type: string;
  segment_index?: number;
  versions: AudioVersion[];
  active_version?: number;
}

interface AudioVersionManagerProps {
  projectId: number;
  segmentCount: number;
  hasOpeningQuote?: boolean;
}

function AudioVersionManager({
  projectId,
  segmentCount,
  hasOpeningQuote = false,
}: AudioVersionManagerProps) {
  const [audioData, setAudioData] = useState<Record<string, AudioVersionGroup>>({});
  const [loading, setLoading] = useState(false);
  const [historyModal, setHistoryModal] = useState(false);
  const [selectedFilename, setSelectedFilename] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [playingAudio, setPlayingAudio] = useState<string | null>(null);

  const audioRefs = useRef<Record<string, HTMLAudioElement>>({});

  // 加载所有音频版本数据
  const loadAllVersions = async () => {
    setLoading(true);
    try {
      const response = await axios.get(
        `${API_BASE_URL}/media-versions/projects/${projectId}/all-versions?media_type=audio`
      );

      const grouped: Record<string, AudioVersionGroup> = {};
      response.data.media.forEach((item: AudioVersionGroup) => {
        grouped[item.filename] = item;
      });

      setAudioData(grouped);
    } catch (error: any) {
      message.error('加载音频版本失败：' + error.message);
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
        `${API_BASE_URL}/media-versions/projects/${projectId}/audio/${filename}/set-active`,
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
        `${API_BASE_URL}/media-versions/projects/${projectId}/audio/${filename}/upload`,
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
    return false;
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

  // 播放/暂停音频
  const handlePlayPause = (url: string) => {
    if (!audioRefs.current[url]) {
      audioRefs.current[url] = new Audio(url);
      audioRefs.current[url].addEventListener('ended', () => {
        setPlayingAudio(null);
      });
    }

    const audio = audioRefs.current[url];

    if (playingAudio === url) {
      audio.pause();
      setPlayingAudio(null);
    } else {
      // 暂停所有其他音频
      Object.values(audioRefs.current).forEach((a) => a.pause());
      audio.play();
      setPlayingAudio(url);
    }
  };

  // 获取活跃版本的URL
  const getActiveVersionUrl = (filename: string): string => {
    const audioGroup = audioData[filename];
    if (!audioGroup || !audioGroup.active_version) {
      return `${API_BASE_URL}/files/${projectId}/audio/${filename}`;
    }

    const activeVersion = audioGroup.versions.find(
      v => v.version === audioGroup.active_version
    );

    return activeVersion?.cloud_url || activeVersion?.local_path || '';
  };

  // 格式化时长
  const formatDuration = (seconds?: number): string => {
    if (!seconds) return '未知';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // 渲染版本历史对话框
  const renderHistoryModal = () => {
    if (!selectedFilename || !audioData[selectedFilename]) {
      return null;
    }

    const audioGroup = audioData[selectedFilename];

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
        width={800}
      >
        <Timeline>
          {audioGroup.versions.map((version) => {
            const audioUrl = version.cloud_url || version.local_path || '';
            const isPlaying = playingAudio === audioUrl;

            return (
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
                        {version.generation_method === 'ai_generated' ? 'TTS生成' : '用户上传'}
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
                  <Space direction="vertical" style={{ width: '100%' }}>
                    {/* 音频播放器 */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                      <Button
                        type="text"
                        size="large"
                        icon={isPlaying ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
                        onClick={() => handlePlayPause(audioUrl)}
                      />
                      <SoundOutlined style={{ fontSize: 24, color: '#1890ff' }} />
                      <div style={{ flex: 1 }}>
                        <audio
                          src={audioUrl}
                          controls
                          style={{ width: '100%', height: 32 }}
                        />
                      </div>
                    </div>

                    {/* 元数据 */}
                    <Row gutter={[16, 8]}>
                      <Col span={12}>
                        <strong>创建时间：</strong>
                        {new Date(version.created_at).toLocaleString('zh-CN')}
                      </Col>
                      <Col span={12}>
                        <strong>创建者：</strong>
                        {version.created_by}
                      </Col>
                      <Col span={12}>
                        <strong>时长：</strong>
                        {formatDuration(version.duration_seconds)}
                      </Col>
                      <Col span={12}>
                        <strong>文件大小：</strong>
                        {(version.file_size_bytes / 1024).toFixed(2)} KB
                      </Col>
                    </Row>

                    {version.generation_params?.voice && (
                        <div>
                          <strong>音色：</strong>
                          {version.generation_params.voice}
                        </div>
                      )}

                    {version.note && (
                      <div>
                        <strong>备注：</strong>
                        {version.note}
                      </div>
                    )}
                  </Space>
                </Card>
              </Timeline.Item>
            );
          })}
        </Timeline>
      </Modal>
    );
  };

  // 渲染音频卡片
  const renderAudioCard = (filename: string, title: string) => {
    const audioGroup = audioData[filename];
    const hasVersions = audioGroup && audioGroup.versions.length > 0;
    const versionCount = audioGroup?.versions.length || 0;
    const activeUrl = getActiveVersionUrl(filename);
    const isPlaying = playingAudio === activeUrl;

    return (
      <Col xs={12} sm={8} md={6} lg={6} key={filename}>
        <Badge count={versionCount} offset={[-10, 10]}>
          <Card
            size="small"
            title={title}
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
                accept="audio/*"
              >
                <Button size="small" icon={<UploadOutlined />} loading={uploading}>
                  上传新版本
                </Button>
              </Upload>,
            ]}
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              {/* 音频播放控制 */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px 0' }}>
                <Button
                  type="primary"
                  shape="circle"
                  size="large"
                  icon={isPlaying ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
                  onClick={() => handlePlayPause(activeUrl)}
                />
              </div>

              <audio
                src={activeUrl}
                controls
                style={{ width: '100%', height: 32 }}
              />

              {hasVersions && audioGroup.active_version && (
                <div style={{ textAlign: 'center', color: '#999', fontSize: 12 }}>
                  当前版本: v{audioGroup.active_version}
                </div>
              )}
            </Space>
          </Card>
        </Badge>
      </Col>
    );
  };

  return (
    <div>
      <Card
        title="音频版本管理"
        extra={
          <Button icon={<ReloadOutlined />} onClick={loadAllVersions} loading={loading}>
            刷新
          </Button>
        }
      >
        <div style={{ marginBottom: 16, color: '#666' }}>
          💡 每个音频可以有多个版本，上传或重新生成会创建新版本，选择一个版本作为活跃版本用于视频合成。
        </div>

        <Row gutter={[16, 16]}>
          {/* 开场音频 */}
          {hasOpeningQuote && renderAudioCard('opening.mp3', '开场音频')}

          {/* 段落音频 */}
          {Array.from({ length: segmentCount }, (_, i) => i + 1).map((segmentIndex) => {
            const filename = `voice_${segmentIndex}.wav`;
            return renderAudioCard(filename, `段落 ${segmentIndex}`);
          })}
        </Row>
      </Card>

      {/* 版本历史对话框 */}
      {renderHistoryModal()}
    </div>
  );
}

export default AudioVersionManager;
