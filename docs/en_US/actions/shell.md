# `shell`

Run a list of shell commands in order.

## Example

```jsonnet
{
  use: 'shell',
  cmds: [
    'echo hello',
    'touch done',
  ],
}
```

## Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `cmds` | `array<string>` | No | Commands to execute sequentially |

## Rules

- Commands in `cmds` run in order
- If any command fails, the current target stops and returns an error
- Each command starts a separate shell, so state from `cd`, `export`, and similar commands does not carry over to the next command
