# `git`

将 Git 仓库克隆到当前 module 工作目录。

## 示例

```python
git(src="https://example.com/repo.git")
```

## 字段

| 字段 | 类型 | 必需 | 说明 |
| --- | --- | --- | --- |
| `src` | `str` | 是 | Git 仓库地址 |
| `path` | `Path` | 否 | 克隆到的目标路径，默认 `Path(".")`，相对路径基于当前 module 工作目录 |
| `branch` | `str` | 否 | 指定分支 |
| `hash` | `str` | 否 | 指定提交哈希；设置后完整克隆并执行 `git checkout`，未设置时用 `--depth=1` 浅克隆 |
