# `shell`

Run a list of shell commands in order.

## Example

```python
shell(cmds=[
    "echo hello",
    "touch done",
])
```

## Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `cmds` | `Sequence[str]` | No | Command list |

## Notes

Each command starts a separate shell, so state from `cd`, `export`, and similar commands does not carry over.
