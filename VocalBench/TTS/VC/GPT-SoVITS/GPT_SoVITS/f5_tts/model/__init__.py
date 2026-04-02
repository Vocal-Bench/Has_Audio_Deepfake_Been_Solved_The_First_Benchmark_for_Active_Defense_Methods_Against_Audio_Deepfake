"""
Compat layer for older f5_tts imports.

旧代码里经常会写：
    from f5_tts.model import CFM

当前仓库只保留了 DiT backbone，这里把 CFM 映射为 DiT，
避免出现 “cannot import name 'CFM' from 'f5_tts.model'” 的错误。
"""

from GPT_SoVITS.f5_tts.model.backbones.dit import DiT as CFM
from GPT_SoVITS.f5_tts.model.backbones.dit import DiT

__all__ = ["CFM", "DiT"]