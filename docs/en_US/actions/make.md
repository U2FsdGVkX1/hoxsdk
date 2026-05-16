# `make`

Run `make` in the current module working directory.

## Example

```python
make(args="defconfig")
```

## Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `args` | `str` | No | Argument string appended after `make` |

## Rules

- The actual command is `make -j$(cpu_count) <args>`
- If `args` is not set, it is equivalent to running parallel `make` directly
