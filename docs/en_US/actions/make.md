# `make`

Run `make` in the current target working directory.

## Example

```jsonnet
{ use: 'make', args: 'defconfig' }
```

## Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `args` | `string` | No | Argument string appended after `make` |

## Rules

- The actual command is `make -j$(cpu_count) <args>`
- If `args` is not set, it is equivalent to running parallel `make` directly
