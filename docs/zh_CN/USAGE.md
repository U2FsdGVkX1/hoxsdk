# Hox SDK 使用指南

## 概览

Hox SDK 根据 board 和 adapter 配置构建产物并打包磁盘镜像。

```sh
python main.py -b <board> -a <adapter>
```

`<board>` 是 `boards/` 下的相对路径，`<adapter>` 是 `adapters/` 下的目录名。

构建阶段在 `build/<board>/<module>/` 中运行模块的 `build` action。镜像阶段格式化分区镜像、运行模块的 `install` 脚本，并将最终磁盘镜像写入 `outputs/<board>/`。

## 需求

Python 依赖：`pydantic` 和 `python-dotenv`（需要 Python 3.10+）。

镜像生成常用工具：`sfdisk`、`dd`、`sudo`、`bash`、`mount`、`umount`。

模块的 `requires` 可能声明额外工具（如 `git`、`patch`、`make` 或交叉编译器）。

## 命令

```sh
python main.py -b <board> -a <adapter>                          # 构建并打包
python main.py -b <board> -a <adapter> --skipimage             # 只运行构建阶段
python main.py -b <board> -a <adapter> --skipbuild              # 只运行镜像阶段
python main.py -b <board> -a <adapter> -p KEY:VALUE             # 传入参数
python main.py -b <board> -a <adapter> -p KEY                  # 设置 KEY=true
python main.py -b <board> -a <adapter> --skipbuild --skipimage --debug  # 只输出配置
python main.py --help                                            # 查看帮助
```

参数文件支持：`python main.py @args.txt`

## 构建参数

`-p`/`--param KEY[:VALUE]` 设置一个参数：可在配置 DSL 中用 `ctx.params["KEY"]` 读取，并作为环境变量 `$KEY` 导出到镜像阶段 install 片段中。

## 命令行选项

| 参数 | 必需 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `-b`, `--board` | 是 | 无 | `boards/` 下的 board 路径 |
| `-a`, `--adapter` | 是 | 无 | `adapters/` 下的 adapter 目录名 |
| `--desktop` | 否 | `minimal` | 桌面配置名 |
| `--skipbuild` | 否 | `false` | 跳过构建阶段 |
| `--skipimage` | 否 | `false` | 跳过镜像阶段 |
| `-p`, `--param KEY[:VALUE]` | 否 | 无 | 设置参数；见构建参数 |
| `--debug [PATTERN]` | 否 | 空 | 输出配置，并在匹配的构建 action 前打开 shell。见调试 |

## 输出

| 路径 | 说明 |
| --- | --- |
| `build/<board>/<module>/` | 模块构建工作目录 |
| `build/<board>/_image/` | 镜像阶段工作目录 |
| `outputs/<board>/` | 生成的磁盘镜像 |
| `logs/<board>/` | 命令日志 |

## 调试

`--debug` 输出最终配置，并在匹配的构建 action 前打开 shell。

```sh
python main.py -b <board> -a <adapter> --debug 'kernel:*' --debug 'uboot:1'
```
