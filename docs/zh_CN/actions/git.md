# `git`

将 Git 仓库克隆到当前 module 工作目录。

## 示例

```python
git(src="https://example.com/repo.git")
```

## 字段

| 字段 | 类型 | 必选 | 说明 |
| --- | --- | --- | --- |
| `src` | `str` | 是 | Git 仓库地址 |
| `path` | `Path` | 否 | 克隆到的目标路径，默认 `Path(".")`，相对路径基于当前 module 工作目录 |
| `branch` | `str` | 否 | 指定分支 |
| `hash` | `str` | 否 | 指定提交哈希，设置后会在克隆完成后执行 `git checkout` |

## 注意

- 未设置 `hash` 时使用 `--depth=1`；设置 `hash` 时完整克隆，并在克隆后执行 checkout。
