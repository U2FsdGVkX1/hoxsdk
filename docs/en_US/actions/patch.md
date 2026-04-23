# `patch`

Apply patch files in order.

## Example

```jsonnet
{
  use: 'patch',
  patches: [BDIR + '/fix.patch'],
}
```

## Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patches` | `array<string>` | No | List of patch files. Paths may be absolute or relative to the current target working directory |
| `gitam` | `bool` | No | When `true`, use `git am`; otherwise use `patch -p1` |

## Rules

- Patches in `patches` are applied in order
- The default command is `patch -p1 < <patch>`
- When `gitam=true`, the command becomes `git am <patch>` and the current working directory must be a Git repository
