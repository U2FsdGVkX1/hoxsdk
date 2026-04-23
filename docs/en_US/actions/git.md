# `git`

Clone a Git repository into the current target working directory.

## Example

```jsonnet
{ use: 'git', src: 'https://example.com/repo.git' }
```

## Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `src` | `string` | Yes | Git repository URL |
| `path` | `string` | No | Destination path for the clone. Default is `.`, and relative paths are resolved from the current target working directory |
| `branch` | `string` | No | Branch to clone |
| `hash` | `string` | No | Commit hash to check out after cloning |

## Rules

- If `hash` is not set, `git clone --depth=1` is used
- If `branch` is set, `-b <branch>` is appended
- If `hash` is set, shallow clone is not used and `git checkout <hash>` runs in the destination directory after cloning
