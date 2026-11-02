# `make`

在当前 module 工作目录中执行 `make`。

## 示例

```python
make(args="defconfig")
```

## 字段

| 字段 | 类型 | 必需 | 说明 |
| --- | --- | --- | --- |
| `args` | `str` | 否 | 追加到 `make -j$(cpu_count)` 后的参数字符串 |
