# Hox SDK 使用文档

## 概览

Hox SDK 根据板级配置和 adapter 脚本构建板级产物并打包磁盘镜像。

一次运行需要选择：

- `boards/<board>/config.jsonnet` 中的一个板级配置。
- `adapters/<adapter>/` 中的一个镜像 adapter。

构建阶段会把产物写入 `outputs/<board>/`。镜像阶段会使用这些产物，并把最终磁盘镜像写入同一个输出目录。



## 需求

根目录 Python 依赖：

- Python 3.10+
- `_jsonnet`
- `pydantic`

镜像生成常用宿主机工具：

- `sfdisk`
- `dd`
- `sudo`
- `bash`
- `mount`
- `umount`

板级 target 可能需要额外工具，例如 `git`、`patch`、`make` 或交叉编译器。请检查所选板级配置中的 `requires`。

依赖安装命令为 Unknown，因为本仓库没有提供根目录包元数据。

## 命令

查看 CLI 帮助：

```sh
python main.py --help
```

构建并打包镜像：

```sh
python main.py -b <board> -a <adapter>
```

只运行构建阶段：

```sh
python main.py -b <board> -a <adapter> --skipimage
```

基于已有输出只运行镜像阶段：

```sh
python main.py -b <board> -a <adapter> --skipbuild
```

输出 Jsonnet 求值后的最终 JSON 配置，不构建、不打包：

```sh
python main.py -b <board> -a <adapter> --skipbuild --skipimage --debug
```

使用参数文件：

```sh
python main.py @args.txt
```

## 参数

| 参数 | 必需 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `-b`, `--board` | 是 | 无 | 相对于 `boards/` 的 board 路径 |
| `-a`, `--adapter` | 是 | 无 | `adapters/` 下的 adapter 目录名 |
| `--desktop` | 否 | `minimal` | 传给镜像脚本的桌面配置名 |
| `--skipbuild` | 否 | `false` | 跳过构建阶段 |
| `--skipimage` | 否 | `false` | 跳过镜像阶段 |
| `--debug [TARGET[:INDEX][,...]]` | 否 | 空；不带值使用时为 `*` | 输出配置，并在匹配的 action 前打开 shell |

## 输出

| 路径 | 说明 |
| --- | --- |
| `build/<board>/<target>/` | 单个 target 的构建工作目录 |
| `build/<board>/_image/` | 镜像阶段工作目录 |
| `outputs/<board>/` | 构建产物和生成的镜像 |
| `logs/<board>/` | 命令日志 |

## 说明

- Board 名称是相对于 `boards/` 的路径。
- Adapter 名称是 `adapters/` 下的目录名。
- 使用 `boards/common.jsonnet` 默认值时，共享的默认最终镜像名是 `sdcard.img`。
- 需要验证：Fedora adapter 的 post 脚本会调用 `chroot_rootfs`，但未找到 Fedora 本地定义。
