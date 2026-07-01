# `cp`

Copy a file or directory to the target location.

## Example

```python
cp(src=ctx.BOARD_DIR / "kernel.config", dest=Path(".config"))
```

## Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `src` | `Path` | Yes | Source path. Absolute paths are allowed; relative paths are resolved from the current module working directory |
| `dest` | `Path` | Yes | Destination path. Absolute paths are allowed; relative paths are resolved from the current module working directory |

## Notes

- Directories are copied recursively and may be merged into existing directories.
