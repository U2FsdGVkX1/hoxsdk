# `patch`

Apply patch files in order.

## Example

```python
patch(patches=[ctx.BOARD_DIR / "fix.patch"])
```

## Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patches` | `Sequence[Path]` | No | List of patch files. Paths may be absolute or relative to the current module working directory |
| `gitam` | `bool` | No | When `true`, use `git am`; otherwise use `patch -p1` |
