# VocalBench Demo Explorer

一个零依赖的本地网站，用来：

- 总结 ICME 论文的 benchmark 设计与主要结论
- 分析 `/home/torfqy/data/vocalbench` 与 `/home/torfqy/data/vocaleval` 的目录结构
- 按防御方法、通道变体、语言、split、克隆模型筛选并试听音频 demo

## 静态上传

当前页面已经改成纯静态版本，直接上传整个目录到 GitHub Pages 即可。

- 根入口页：`/index.html`
- 前端资源：`/static`
- 音频与页面数据：`/demo_assets`

页面不再依赖 `/api/pipeline` 和 `/media`，GitHub Pages 可直接访问。

## 本地预览

```bash
cd /home/torfqy/data/Vocal_Bench_demo
python server.py
```

默认地址：

```text
http://127.0.0.1:8123
```

## 说明

- 服务端会在启动时扫描 `vocalbench` / `vocaleval` 的 `info_*.csv`
- 静态页面实际读取的是预先生成好的 `demo_assets/pipeline.json`
- 页面里已内置样本总说明、variant 含义解释，以及可试听的结果卡片
