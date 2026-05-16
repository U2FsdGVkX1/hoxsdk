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
| `cmds` | `Sequence[str]` | No | Commands to execute sequentially |

## Rules

- Commands in `cmds` run in order
- If any command fails, the current module stops and returns an error
- Each command starts a separate shell, so state from `cd`, `export`, and similar commands does not carry over to the next command
