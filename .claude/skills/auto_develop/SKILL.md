---
name: auto_develop
description: |
  SmartClaw 项目自动化开发技能。当用户说以下内容时触发：
  - "开始开发 smartclaw" / "开始 smartclaw 开发"
  - "继续开发 smartclaw" / "继续 smartclaw 开发"
  - "auto dev" / "start dev" / "自动开发"
  - "继续开发" / "开始开发"（在 smartclaw 项目上下文中）
  - 提及任务编号（如 A3, B5）

  此技能执行 TDD 开发流程，每个任务完成后等待用户确认。
---

# SmartClaw 自动开发技能

## 技能作用

此技能用于自动化 SmartClaw 项目的开发流程。它会：
1. 自动读取项目定位和开发进度
2. 按规则选择下一个待开发任务
3. 执行完整的 TDD 开发循环（Red-Green-Refactor）
4. 自动更新开发进度文档
5. 确保 code quality（ruff、mypy）

**核心特点**：TDD 开发流程自动化，每个任务完成后等待用户确认。

---

## 核心原则

**重要**：每个任务开发完毕后，更新完 Develop_schedule.md 文档后，**必须停止实施**，等待用户确认后续动作。

用户需要确认：
1. 是否提交 Git？
2. 是否继续下一个任务？
3. 是否有其他需要调整的内容？

**禁止**在用户确认前自动执行 Git 提交或继续下一个任务。

### 环境隔离铁律

**重要**：任何开发任务开始前，必须确保已进入项目虚拟环境。

**执行规则**：
1. **首次开发**：先完成任务 A13（创建 uv 虚拟环境并安装依赖）
2. **后续开发**：在执行任何任务前，先激活虚拟环境
   ```bash
   source .venv/bin/activate  # Linux/macOS
   # 或
   .venv\Scripts\activate     # Windows
   ```
3. **测试运行**：使用 `pytest` 或 `uv run pytest` 确保在隔离环境中运行
4. **代码检查**：使用 `ruff check` 和 `mypy` 确保在隔离环境中运行

**禁止**：在未激活虚拟环境的情况下执行开发、测试或代码检查任务。

---

## 必读文档（每次开发前必须阅读）

以下两个文件在**每次开发会话开始时必须阅读**：

| 文档 | 位置 | 作用 |
|-----|------|------|
| One_page.md | .claude/skills/auto_develop/references/One_page.md | 项目最终目标、核心定位，确保开发方向正确 |
| Develop_schedule.md | .claude/skills/auto_develop/references/Develop_schedule.md | 开发进度、任务列表、更新规则 |

**重要**：阅读 One_page.md 是为了记住项目的最终目标和核心定位，保证开发方向正确。

---

## Git 配置与分支策略

### 项目 Git 配置

| 配置项 | 值 |
|-------|-----|
| 仓库地址 | https://github.com/LevyLee18/SmartClaw |
| 主分支 | main |
| 提交规范 | Conventional Commits |
| 分支策略 | 功能分支（按模块） |

### 分支命名规则

| 模块 | 分支名 |
|-----|-------|
| A: 基础设施与配置 | feature/A |
| B: Memory 模块 | feature/B |
| C: RAG 模块 | feature/C |
| D: 内置工具模块 | feature/D |
| E: Agent 模块 | feature/E |
| F: FastAPI 接口 | feature/F |
| G: 系统集成测试 | feature/G |
| H: 初始化与启动 | feature/H |

### Git 工作流

```
1. 开始模块开发
   → git checkout -b feature/{模块名}

2. 完成任务后提交
   → git add .claude/skills/auto_develop/references/Develop_schedule.md backend/ tests/
   → git commit -m "feat({模块}): 完成任务 {任务编号} - {任务名称}"
   → git push -u origin feature/{模块名}  (首次推送)
   → git push  (后续推送)

3. 模块全部完成后合并
   → git checkout main
   → git merge feature/{模块名}
   → git push origin main
```

---

## 开发流程

### Phase 0：初始化（每次必做）

```
步骤 0.1：读取 .claude/skills/auto_develop/references/One_page.md
→ 理解项目定位：轻量级透明记忆文件管理系统
→ 记住核心设计哲学：File-first Memory, Skills as Plugins, 透明可控
→ 明确最终目标，确保开发方向正确

步骤 0.2：读取 .claude/skills/auto_develop/references/Develop_schedule.md
→ 查看「模块进度汇总」，确认当前进度
→ 找到当前模块（未完成率最高的模块）
```

### Phase 1：任务选择

**任务挑选规则**（按优先级）：

1. **模块顺序**：严格按 A → B → C → D → E → F → G → H 顺序，不跳模块
2. **模块内顺序**：在当前模块内，按编号顺序选择第一个未开始的任务
3. **进度标记规则**：
   - `[ ]` → 未开始，可被选中
   - `[*]` → 进行中，继续该任务
   - `[x]` → 已完成，跳过
   - `[!]` → 阻塞中，跳过并记录原因

4. **特殊规则**：
   - A1、A2 是基础设施任务：
     - 无需 TDD 循环，直接创建目录结构
     - 更新 Develop_schedule.md 标记为 `[x]`
     - **完成后同样需要等待用户确认**（是否提交 Git、是否继续下一个任务）
   - Tx 是纯测试项，在对应模块完成后执行
   - Ix 是集成验证项，在对应模块完成后执行
   - Gx 是端到端测试项，在所有模块完成后执行

```
任务选择算法：
1. 读取 Develop_schedule.md 中的「模块进度汇总」
2. 按顺序遍历模块 A → B → C → D → E → F → G → H
3. 找到第一个「未完成」数 > 0 的模块
4. 在该模块的任务表中，找到第一个标记为 `[ ]` 的任务
5. 如果有 `[*]` 的任务，优先继续该任务
6. 返回任务编号和任务信息

步骤 1.3：标记任务为进行中
→ 在 Develop_schedule.md 中，将选中任务的 `开发进度` 从 `[ ]` 改为 `[*]`
→ 这确保如果开发过程中断，下次可以继续该任务
```

### Phase 2：阅读规范

```
步骤 2.1：读取任务详情
→ 从 Develop_schedule.md 获取任务的「开发功能描述」
→ 获取「关联DEV_SPEC」定位

步骤 2.2：读取模块参考文档
→ 读取 .claude/skills/auto_develop/references/module_X.md
→ 获取接口定义、数据模型、实现规范

步骤 2.3：读取关联模块概览
→ 查阅本文档末尾的「模块关联参考索引」
→ 如果当前任务涉及其他模块，读取关联模块文档的「接口概述」部分
→ 重点理解：数据流方向、接口参数、返回值格式
```

### Phase 3：TDD 开发循环（Red-Green-Refactor）

#### 3.1 Red（先写失败的测试）

```
1. 根据任务的「开发功能描述」分析测试要点
2. 创建测试文件：
   - 位置：tests/unit/{模块}/test_{文件名}.py
   - 命名规则：test_{被测试类名}.py
3. 编写测试用例，覆盖：
   - 正常场景（happy path）
   - 边界场景（boundary cases）
   - 异常场景（error cases）
4. 运行测试：pytest {测试文件路径}
5. 确认测试失败（因为功能未实现）
```

#### 3.2 Green（写最少代码使测试通过）

```
1. 创建源代码文件：
   - 位置：backend/{模块}/{文件名}.py
2. 编写最少代码，使测试通过
3. 运行测试：pytest {测试文件路径}
4. 确认全部测试通过
```

#### 3.3 Refactor（重构优化）

```
1. 运行代码检查：ruff check backend/
2. 运行类型检查：mypy backend/
3. 重构代码，确保测试仍然通过
4. 添加文档字符串（如果缺失）
```

### Phase 4：更新进度

**更新 Develop_schedule.md**：

```
步骤 4.1：更新任务状态
→ 将任务行的 `开发进度` 从 `[*]` 改为 `[x]`
→ 在 `任务完成日期` 列填写日期（格式：YYYY-MM-DD）
→ 在 `备注` 列填写：按计划完成 / 或遇到的问题和解决方案

步骤 4.2：更新模块进度汇总
→ 在「模块进度汇总」表中：
  - 对应模块的「已完成」数 +1
  - 对应模块的「未完成」数 -1
  - 更新「完成率」百分比（已完成/总任务数*100%）

步骤 4.3：如果模块全部完成
→ 在备注中标记：模块 X 开发完成
```

### Phase 5：等待用户确认（必须）

**完成 Phase 4 后，必须停止并等待用户确认。**

向用户展示：
1. **任务完成摘要**：任务编号、任务名称、完成日期
2. **建议的 Git 提交命令**（功能分支模式）：
   ```bash
   # 确保在正确的功能分支上
   git checkout feature/{当前模块}

   # 暂存文件
   git add .claude/skills/auto_develop/references/Develop_schedule.md backend/ tests/

   # 本地提交
   git commit -m "feat({模块}): 完成任务 {任务编号} - {任务名称}"

   # 推送到远程（用户确认后执行）
   git push origin feature/{当前模块}
   ```
3. **下一个待开发任务**：任务编号和任务名称

询问用户：
- 是否执行 Git 提交？
- 是否推送到远程？
- 是否继续下一个任务？
- 是否有其他需要调整的内容？

**模块完成时的额外确认**：
如果当前模块的所有任务已完成，询问用户是否将功能分支合并到 main：
```bash
git checkout main
git merge feature/{模块名}
git push origin main
```

**禁止**在用户确认前自动执行 Git 提交、推送或继续下一个任务。

---

## 完整开发示例

### 示例：自动开发任务 A3（LLMConfig）

```
【用户输入】
继续 smartclaw 开发

【技能执行 - Phase 0：初始化】

→ 读取 .claude/skills/auto_develop/references/One_page.md...
  ✓ 项目定位：轻量级透明记忆文件管理系统
  ✓ 核心哲学：File-first Memory（文件即记忆）
  ✓ 核心哲学：Skills as Plugins（技能即插件）
  ✓ 核心哲学：透明可控（拒绝黑盒 Agent）
  ✓ 最终目标：让 AI Agent 的记忆像普通文件一样透明可控

→ 读取 .claude/skills/auto_develop/references/Develop_schedule.md...
  ✓ 当前进度：0%（0/135 已完成）
  ✓ 当前模块：模块 A（基础设施与配置）
  ✓ 模块 A 进度：0/15 完成

【技能执行 - Phase 1：任务选择】

→ 应用任务挑选规则：
  1. 按模块顺序：A（当前）→ B → C → ...
  2. 模块 A 任务列表：
     | 编号 | 开发进度 |
     | A1   | [ ]      | ← 未开始
     | A2   | [ ]      |
     | A3   | [ ]      |
     ...
  3. 选择第一个 `[ ]` 任务：A1

→ 检测到 A1 是基础设施任务（备注：基础设施，无需TDD）
→ 跳过 A1，继续选择下一个...

→ 选择任务：A3（测试并实现 LLMConfig）
→ 将 A3 标记为 `[*]` 进行中

【技能执行 - Phase 2：阅读规范】

→ 读取 A3 任务详情：
  - 开发内容：测试并实现 LLMConfig
  - 开发功能描述：
    **测试**: 验证字段类型、范围校验（max_tokens 1-100000, temperature 0-2）、
            无效值抛 ValidationError
    **实现**: Pydantic 模型，包含 provider, model, api_key, max_tokens, temperature
  - 关联DEV_SPEC：4.5.1, 行3568
  - 验收标准：1.测试覆盖所有验证规则 2.测试通过 3.无效值正确抛异常

→ 读取 .claude/skills/auto_develop/references/module_A.md...
  ✓ LLMConfig 接口定义
  ✓ 字段类型规范
  ✓ 验证规则详情

【技能执行 - Phase 3：TDD 开发循环】

→ [3.1 Red] 创建测试文件
  创建：tests/unit/config/test_models.py

```python
"""测试 LLMConfig 模型"""
import pytest
from pydantic import ValidationError


class TestLLMConfig:
    """LLMConfig 测试类"""

    def test_valid_config(self):
        """测试有效配置"""
        from backend.config.models import LLMConfig

        config = LLMConfig(
            provider="anthropic",
            model="claude-3-opus",
            api_key="sk-test-key",
            max_tokens=4096,
            temperature=0.7
        )
        assert config.provider == "anthropic"
        assert config.model == "claude-3-opus"
        assert config.max_tokens == 4096
        assert config.temperature == 0.7

    def test_max_tokens_below_range(self):
        """测试 max_tokens 低于范围（边界场景）"""
        from backend.config.models import LLMConfig

        with pytest.raises(ValidationError) as exc_info:
            LLMConfig(
                provider="anthropic",
                model="claude-3-opus",
                api_key="sk-test-key",
                max_tokens=0,  # 低于最小值 1
                temperature=0.7
            )
        assert "max_tokens" in str(exc_info.value)

    def test_max_tokens_above_range(self):
        """测试 max_tokens 超出范围（边界场景）"""
        from backend.config.models import LLMConfig

        with pytest.raises(ValidationError):
            LLMConfig(
                provider="anthropic",
                model="claude-3-opus",
                api_key="sk-test-key",
                max_tokens=100001,  # 超过最大值 100000
                temperature=0.7
            )

    def test_temperature_below_range(self):
        """测试 temperature 低于范围（边界场景）"""
        from backend.config.models import LLMConfig

        with pytest.raises(ValidationError):
            LLMConfig(
                provider="anthropic",
                model="claude-3-opus",
                api_key="sk-test-key",
                max_tokens=4096,
                temperature=-0.1  # 低于最小值 0
            )

    def test_temperature_above_range(self):
        """测试 temperature 超出范围（边界场景）"""
        from backend.config.models import LLMConfig

        with pytest.raises(ValidationError):
            LLMConfig(
                provider="anthropic",
                model="claude-3-opus",
                api_key="sk-test-key",
                max_tokens=4096,
                temperature=2.1  # 超过最大值 2
            )

    def test_missing_required_field(self):
        """测试缺少必填字段（异常场景）"""
        from backend.config.models import LLMConfig

        with pytest.raises(ValidationError):
            LLMConfig(
                provider="anthropic",
                model="claude-3-opus",
                # 缺少 api_key
                max_tokens=4096,
                temperature=0.7
            )
```

→ 运行测试：pytest tests/unit/config/test_models.py
→ 结果：6 failed（预期失败，功能未实现）✓

→ [3.2 Green] 创建源代码文件
  创建：backend/config/models.py

```python
"""配置数据模型"""
from typing import Optional
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM 配置模型"""

    provider: str = Field(..., description="LLM 提供商")
    model: str = Field(..., description="模型名称")
    api_key: str = Field(..., description="API 密钥")
    max_tokens: int = Field(
        default=4096,
        ge=1,
        le=100000,
        description="最大 token 数"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="温度参数"
    )
```

→ 运行测试：pytest tests/unit/config/test_models.py
→ 结果：6 passed ✓

→ [3.3 Refactor] 代码质量检查
→ 运行 ruff check backend/config/models.py
→ 结果：无警告 ✓

→ 运行 mypy backend/config/models.py
→ 结果：通过 ✓

→ 检查文档字符串：已完整 ✓

【技能执行 - Phase 4：更新进度】

→ 更新 Develop_schedule.md：
  - 任务 A3：`[*]` → `[x]`
  - 任务完成日期：2026-03-22
  - 备注：按计划完成

→ 更新模块进度汇总：
  | 模块 | 已完成 | 未完成 | 完成率 |
  | A    | 1      | 14     | 7%     |
  | 总计 | 1      | 134    | 1%     |

【技能执行 - Phase 5：等待用户确认】

→ 任务 A3 已完成，Develop_schedule.md 已更新

→ 请确认后续动作：
  1. 是否执行 Git 提交？
     git add .claude/skills/auto_develop/references/Develop_schedule.md backend/ tests/
     git commit -m "feat: 完成任务 A3 - 测试并实现 LLMConfig"
  2. 是否继续下一个任务：A4（测试并实现 ContainerConfig）？
  3. 是否有其他需要调整的内容？

→ 等待用户确认...
```

---

## 参考文档

**所有参考文档均位于**：`.claude/skills/auto_develop/references/`

### 必读文档
| 文件 | 说明 | 读取时机 |
|-----|------|---------|
| Develop_schedule.md | 开发进度、任务列表、更新规则 | 每次开发开始时 |
| One_page.md | 项目定位、核心设计哲学、最终目标 | 每次开发开始时 |

### 模块参考文档
| 文件 | 说明 | 读取时机 |
|-----|------|---------|
| module_A.md | 模块 A：基础设施与配置 | 开发模块 A 任务时 |
| module_B.md | 模块 B：Memory 模块 | 开发模块 B 任务时 |
| module_C.md | 模块 C：RAG 模块 | 开发模块 C 任务时 |
| module_D.md | 模块 D：内置工具模块 | 开发模块 D 任务时 |
| module_E.md | 模块 E：Agent 模块 | 开发模块 E 任务时 |
| module_F.md | 模块 F：FastAPI 接口 | 开发模块 F 任务时 |
| module_G.md | 模块 G：系统集成测试 | 开发模块 G 任务时 |
| module_H.md | 模块 H：初始化与启动 | 开发模块 H 任务时 |

### 模块关联参考索引

开发某模块时，如有必要请同步阅读关联模块文档的「接口概述」部分：

| 开发模块 | 关联模块 | 关联原因 |
|---------|---------|---------|
| A（基础设施） | - | 无依赖 |
| B（Memory） | A | 配置依赖 |
| C（RAG） | A | 配置依赖 |
| D（内置工具） | B、C | 记忆工具依赖 |
| E（Agent） | A、B、C、D | 整合所有模块 |
| F（FastAPI） | A、E | 依赖 Agent |
| G（集成测试） | 按需 | 测试范围决定 |
| H（初始化） | 全部 | 启动流程 |
