# Vocus TTS 模型

## 模型说明

Vocus是一个商业化的TTS API服务，提供高质量的语音克隆功能。

## 部署方式

Vocus通过API调用使用，不需要本地模型文件。

### API端点

- 创建语音角色: `https://v1.vocu.ai/api/tts/voice`
- 生成音频: `https://v1.vocu.ai/api/tts/simple-generate`

### 使用方式

模型通过VoiceKit封装使用：

```python
from VoiceKit import AVAILABLE_TTS_MODELS

vocus_model = AVAILABLE_TTS_MODELS['Vocus']
result = vocus_model.infer(
    ref_audio="reference.wav",
    gen_text="要生成的文本"
)
```

## 模型版本

- **v2.9**: 用于中文/英文
- **v3.0**: 用于其他语言

## 特性

- 支持多语言（zh, en, es等）
- 自动音频裁剪（超过20MB会自动裁剪）
- Voice ID缓存机制
- 错误处理：自动跳过 `VOICE_ACTIVE_DETECT_FAILURE` 和 `MINIMUM_DURATION_NOT_MET` 错误

## 相关链接

- Vocus官网: https://vocu.ai

## 配置

- API Key: 存储在模型文件中
- 并发数: 5
- 请求延迟: 5.0秒
