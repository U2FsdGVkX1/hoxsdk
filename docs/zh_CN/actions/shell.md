# `shell`

按顺序执行 Shell 命令列表。

## 示例

```python
shell(cmds=[
    "echo hello",
    "touch done",
])
```

## 字段

| 字段 | 类型 | 必选 | 说明 |
| --- | --- | --- | --- |
| `cmds` | `Sequence[str]` | 否 | 需要依次执行的命令列表 |

## 注意

- 命令按顺序执行。每条命令都会启动独立 Shell，`cd`、`export` 等状态不会传递。
