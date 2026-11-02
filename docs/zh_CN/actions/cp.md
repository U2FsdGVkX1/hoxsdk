# `cp`

将文件或目录复制到目标位置。

## 示例

```python
cp(src=ctx.BOARD_DIR / "kernel.config", dest=Path(".config"))
```

## 字段

| 字段 | 类型 | 必需 | 说明 |
| --- | --- | --- | --- |
| `src` | `Path` | 是 | 源路径，可使用绝对路径；相对路径相对于当前 module 工作目录 |
| `dest` | `Path` | 是 | 目标路径，可使用绝对路径；相对路径相对于当前 module 工作目录 |

## 注意

目录会递归复制，并允许合并到已存在目录。
