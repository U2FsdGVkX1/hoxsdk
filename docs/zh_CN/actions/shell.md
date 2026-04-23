# `shell`

按顺序执行 Shell 命令列表

## 示例

```jsonnet
{
  use: 'shell',
  cmds: [
    'echo hello',
    'touch done',
  ],
}
```

## 字段

| 字段 | 类型 | 必选 | 说明 |
| --- | --- | --- | --- |
| `cmds` | `array<string>` | 否 | 需要依次执行的命令列表 |

## 规则

- `cmds` 中的命令按顺序执行
- 任意命令失败时，当前 target 会中止并报错
- 每条命令都会启动独立的 Shell；`cd`、`export` 等状态不会传递到下一条命令
