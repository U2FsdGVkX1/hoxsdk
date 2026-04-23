# `cp`

Copy a file or directory to the target location.

## Example

```jsonnet
{ use: 'cp', src: BDIR + '/kernel.config', dest: '.config' }
```

## Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `src` | `string` | Yes | Source path. Absolute paths are allowed; relative paths are resolved from the current target working directory |
| `dest` | `string` | Yes | Destination path. Absolute paths are allowed; relative paths are resolved from the current target working directory |

## Rules

- If `src` is a directory, a directory copy is performed and it may be merged into an existing directory
- If `src` is a file, a single-file copy is performed and file metadata is preserved
