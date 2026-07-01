# `patch`

按顺序应用补丁文件。

## 示例

```python
patch(patches=[ctx.BOARD_DIR / "fix.patch"])
```

## 字段

| 字段 | 类型 | 必选 | 说明 |
| --- | --- | --- | --- |
| `patches` | `Sequence[Path]` | 否 | 补丁文件列表，补丁路径可使用绝对路径，也可使用相对当前 module 工作目录的路径 |
| `gitam` | `bool` | 否 | 为 `true` 时使用 `git am`，否则使用 `patch -p1` |

## 注意

- 补丁按顺序用 `patch -p1` 应用；`gitam=true` 时改用 `git am`。
