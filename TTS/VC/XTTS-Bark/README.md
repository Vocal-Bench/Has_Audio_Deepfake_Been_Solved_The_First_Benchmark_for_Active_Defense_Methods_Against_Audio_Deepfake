# XTTS/Bark TTS 模型

## 模型说明

- **XTTS**: Coqui TTS的XTTS模型，支持多语言零样本语音克隆
- **Bark**: Coqui TTS的Bark模型，支持文本转语音和音效生成

## 部署方式

这两个模型通过 `TTS` (Coqui TTS) Python包提供。

### 安装方式

```bash
pip install TTS
```

### 使用方式

模型通过VoiceKit封装使用：

```python
from VoiceKit import AVAILABLE_TTS_MODELS

# 使用XTTS模型
xtts_model = AVAILABLE_TTS_MODELS['XTTS']
result = xtts_model.infer(
    ref_audio="reference.wav",
    gen_text="要生成的文本"
)

# 使用Bark模型
bark_model = AVAILABLE_TTS_MODELS['Bark']
result = bark_model.infer(
    ref_audio="reference.wav",
    gen_text="要生成的文本"
)
```

## 模型存储位置

模型文件存储在：`/home/torfqy/data/tts_models/`

## 相关链接

- Coqui TTS GitHub: https://github.com/coqui-ai/TTS
- XTTS文档: https://github.com/coqui-ai/TTS/wiki/XTTS-v2
- Bark文档: https://github.com/coqui-ai/TTS/wiki/Bark

## 环境配置

- Conda环境: `voicekit`
- 支持多语言
- 使用HuggingFace镜像: `https://hf-mirror.com`
