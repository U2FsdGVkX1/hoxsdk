# `make`

Run `make` in the current module working directory.

## Example

```python
make(args="defconfig")
```

## Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `args` | `str` | No | Argument string appended after `make -j$(cpu_count)` |
