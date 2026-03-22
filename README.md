# SmartClaw

轻量级透明记忆文件管理系统

## 简介

SmartClaw 让 AI Agent 的记忆像普通文件一样透明可控。

## 核心特性

- **File-first Memory** - 文件即记忆，摒弃不透明的向量数据库
- **Skills as Plugins** - 技能即插件，拖入即用
- **透明可控** - 所有操作对开发者完全透明

## 安装

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

## 开发

```bash
# 运行测试
pytest

# 代码检查
ruff check backend/
mypy backend/
```
