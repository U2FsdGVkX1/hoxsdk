# `make`

在当前 module 工作目录中执行 `make`。

## 示例

```python
make(args="defconfig")
```

## 字段

| 字段 | 类型 | 必选 | 说明 |
| --- | --- | --- | --- |
| `args` | `str` | 否 | 追加到 `make` 后的参数字符串 |

## 注意

- 实际执行形式为 `make -j$(cpu_count) <args>`。
