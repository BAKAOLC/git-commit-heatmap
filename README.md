# Git Commit Heatmap

生成 Git 提交时间网格表工具，以日期为横坐标，小时为纵坐标，显示每天在哪些时间段有提交。

## 使用方法

### 安装依赖

使用 [uv](https://github.com/astral-sh/uv) 管理 Python 环境：

```bash
uv sync
```

### 基本用法

#### 统计当前仓库

```bash
uv run main.py
```

#### 统计多个仓库

```bash
uv run main.py --repo /path/to/repo1 --repo /path/to/repo2 --repo /path/to/repo3
```

#### 时间过滤选项

```bash
# 只显示最近90天的提交
uv run main.py --days 90

# 指定时间范围（从某个日期到某个日期）
uv run main.py --since "2024-01-01" --until "2024-12-31"

# 使用相对时间
uv run main.py --since "2 weeks ago" --until "1 week ago"
```

#### 作者过滤

```bash
# 只显示指定作者的提交（支持正则表达式）
uv run main.py --author "John Doe"
uv run main.py --author "John"
```

#### 生成 HTML 文件

```bash
uv run main.py --html output.html
```

#### 完整示例

```bash
# 统计多个仓库，过滤作者，指定时间范围，生成HTML
uv run main.py --repo ../repo1 --repo ../repo2 --author "John" --since "2024-01-01" --html output.html
```

## 输出说明

- **横坐标**: 日期（月-日）
- **纵坐标**: 小时（0-23时）
- **数值**: 该日期该小时的提交次数
- **统计信息**: 总提交数、各仓库贡献、最活跃时段等

