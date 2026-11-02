# `patch`

按顺序应用补丁文件。

## 示例

```python
patch(patches=[ctx.BOARD_DIR / "fix.patch"])
```

## 字段

| 字段 | 类型 | 必需 | 说明 |
| --- | --- | --- | --- |
| `patches` | `Sequence[Path]` | 否 | 补丁文件列表，可使用绝对路径或相对当前 module 工作目录的路径 |
| `gitam` | `bool` | 否 | 为 `true` 时使用 `git am`，否则使用 `patch -p1` |
