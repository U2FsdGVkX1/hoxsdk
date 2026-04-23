# `make`

在当前 target 工作目录中执行 `make`

## 示例

```jsonnet
{ use: 'make', args: 'defconfig' }
```

## 字段

| 字段 | 类型 | 必选 | 说明 |
| --- | --- | --- | --- |
| `args` | `string` | 否 | 追加到 `make` 后的参数字符串 |

## 规则

- 实际执行形式为 `make -j$(cpu_count) <args>`
- 未设置 `args` 时，等价于直接执行并行 `make`
