# E2/F5 TTS 模型

## 模型说明

- **E2**: E2TTS 文本转语音模型
- **F5**: F5-TTS 文本转语音模型

## 部署方式

这两个模型通过 `f5-tts` Python包提供，不需要单独的GitHub仓库。

### 安装方式

```bash
pip install f5-tts
```

### 使用方式

模型通过VoiceKit封装使用：

```python
from VoiceKit import AVAILABLE_TTS_MODELS

# 使用E2模型
e2_model = AVAILABLE_TTS_MODELS['E2']
result = e2_model.infer(
    ref_audio="reference.wav",
    gen_text="要生成的文本",
    ref_text="参考文本"
)

# 使用F5模型
f5_model = AVAILABLE_TTS_MODELS['F5']
result = f5_model.infer(
    ref_audio="reference.wav",
    gen_text="要生成的文本",
    ref_text="参考文本"  # F5需要参考文本
)
```

## 相关链接

- F5-TTS GitHub: https://github.com/SWivid/F5-TTS

## 环境配置

- Conda环境: `e2f5`
- Python版本: 3.10
- GPU: GPU 0-4 (多GPU支持)
