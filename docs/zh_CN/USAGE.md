# Hox SDK 使用文档

## 常用命令

| 用途 | 命令 |
| --- | --- |
| 默认构建并打包镜像 | `python main.py -b QEMU/Generic -a alpine` |
| 仅执行构建阶段 | `python main.py -b QEMU/Generic -a alpine --skipimage` |
| 复用已有产物重新打包镜像 | `python main.py -b QEMU/Generic -a alpine --skipbuild` |

- `board` 的取值为 `boards/` 下的相对路径，例如 `QEMU/Generic`
- `adapter` 的取值为 `adapters/` 下的目录名，例如 `fedora`

## 参数

| 参数 | 必选 | 说明 |
| --- | --- | --- |
| `-b`, `--board` | 是 | 板级配置，相对于 `boards/` 的路径 |
| `-a`, `--adapter` | 是 | 镜像适配器，对应 `adapters/<adapter>/` |
| `--desktop` | 否 | 传递给镜像脚本的桌面配置名，默认 `minimal` |
| `--skipbuild` | 否 | 跳过构建阶段，只执行镜像阶段 |
| `--skipimage` | 否 | 跳过镜像阶段，只执行构建阶段 |
| `--debug` | 否 | 在指定 `target/action` 前进入调试 Shell，格式见 [DEVELOPER.md](./DEVELOPER.md#调试) |

## 输出

| 路径 | 说明 |
| --- | --- |
| `build/<board>/<target>/` | target 工作目录 |
| `build/<board>/_image/` | 镜像阶段的临时工作目录 |
| `outputs/<board>/` | 构建产物和镜像输出目录 |
| `logs/<board>/` | 命令日志目录，例如 `kernel.log`、`_image.log` |

构建阶段 `result` 匹配到的文件会被移动到 `outputs/<board>/` 根目录，构建日志位于 `logs/<board>/`
