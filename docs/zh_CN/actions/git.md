# `git`

将 Git 仓库克隆到当前 target 工作目录

## 示例

```jsonnet
{ use: 'git', src: 'https://example.com/repo.git' }
```

## 字段

| 字段 | 类型 | 必选 | 说明 |
| --- | --- | --- | --- |
| `src` | `string` | 是 | Git 仓库地址 |
| `path` | `string` | 否 | 克隆到的目标路径，默认 `.`，相对路径基于当前 target 工作目录 |
| `branch` | `string` | 否 | 指定分支 |
| `hash` | `string` | 否 | 指定提交哈希，设置后会在克隆完成后执行 `git checkout` |

## 规则

- 未设置 `hash` 时使用 `git clone --depth=1`
- 设置 `branch` 时会附加 `-b <branch>`
- 设置 `hash` 时不使用浅克隆，并在目标目录执行 `git checkout <hash>`
