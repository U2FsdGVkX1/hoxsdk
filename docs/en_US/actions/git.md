# `git`

Clone a Git repository into the current module working directory.

## Example

```python
git(src="https://example.com/repo.git")
```

## Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `src` | `str` | Yes | Git repository URL |
| `path` | `Path` | No | Destination path for the clone. Default is `Path(".")`; relative paths are resolved from the current module working directory |
| `branch` | `str` | No | Branch to clone |
| `hash` | `str` | No | Commit hash to check out after cloning |

## Rules

- If `hash` is not set, `git clone --depth=1` is used
- If `branch` is set, `-b <branch>` is appended
- If `hash` is set, shallow clone is not used and `git checkout <hash>` runs in the destination directory after cloning
