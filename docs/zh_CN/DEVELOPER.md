# Hox SDK 开发者文档

## 概念

SDK 通过组合 **board 配置** 和 **adapter 配置** 驱动构建与镜像生成。

- **Board 配置** (`boards/<board>/config.py`)：定义架构、分区、镜像和模块列表。
- **Adapter 配置** (`adapters/<adapter>/config.py`)：提供发行版相关模块。
- **Module**：构建 (`build`) 与安装 (`install`) 的可插拔单元，通过 `build_after`、`build_before`、`install_after` 和 `install_before` 控制执行顺序。
- **Action**：模块的构建 action，实现见 `actions/`，字段文档见 `docs/zh_CN/actions/`。
- **Install 片段**：模块的安装单元，在镜像生成阶段运行，用于定制 rootfs。

运行命令：

```sh
python main.py -b <board> -a <adapter>
```

`<board>` 是 `boards/` 下的相对路径，`<adapter>` 是 `adapters/` 下的目录名。

## 编写 Board 配置

Board 配置是 Python DSL 文件，导出 `configure(ctx) -> Board`。`ConfigContext` 主要属性：

- `ctx.adapter` — 加载当前选择的 adapter 模块列表。
- `ctx.module(name, *args)` — 加载 board 本地模块：执行 `modules/<name>/config.py`，返回其 `configure(ctx, *args)`。
- `ctx.params` — 通过 `-p KEY:VALUE` CLI 选项设置的参数映射；用 `ctx.params["KEY"]` 读取。
- `ctx.BOARD_DIR` — board 目录绝对路径；用 `ctx.BOARD_DIR / "file"` 引用 board 本地文件。
- `ctx.ADAPTER_DIR` — adapter 目录绝对路径；用 `ctx.ADAPTER_DIR / "file"` 引用 adapter 本地文件（主要在 adapter 配置中使用）。
- `ctx.ADAPTER_NAME` — 当前 adapter 名称字符串。

最小 board 配置：

```python
from boards.common import default_images, default_partitions
from hox import Board, ConfigContext


def configure(ctx: ConfigContext) -> Board:
    arch = "riscv64"
    return Board(
        arch=arch,
        partitions=default_partitions(),
        images=default_images(),
        modules=ctx.adapter,
    )
```

### 顶层字段

| 字段 | 必需 | 用途 |
| --- | --- | --- |
| `arch` | 镜像生成时 | 目标架构，作为 `ARCH` 传入安装脚本 |
| `partitions` | 否 | 分区镜像定义 |
| `images` | 否 | 最终磁盘镜像定义 |
| `modules` | 否 | 构建和安装模块列表 |

### `partitions` 字段

| 字段 | 必需 | 用途 |
| --- | --- | --- |
| `name` | 是 | 分区镜像文件名 |
| `size` | 是 | 分区大小（512 字节扇区数） |
| `mkfs` | 是 | 文件系统命令，例如 `mkfs.ext4` |
| `mountpoint` | 是 | 临时 rootfs 内的挂载点 |

### `images` 字段

| 字段 | 必需 | 用途 |
| --- | --- | --- |
| `name` | 是 | 最终镜像文件名，位于 `outputs/<board>/` |
| `table` | 否 | 分区表类型：`gpt` 或 `dos`；默认是 `gpt` |
| `partitions` | 是 | 最终镜像中的分区引用列表，顺序即分区顺序 |

### `images[].partitions` 字段

| 字段 | 必需 | 用途 |
| --- | --- | --- |
| `name` | 是 | 分区镜像文件名 |
| `start` | 否 | 起始偏移（512 字节扇区数）；省略时接在上一个分区后，1 MiB 对齐 |
| `size` | 否 | 大小（扇区数）；省略时从分区镜像文件推断 |
| `type` | 否 | 传给 `sfdisk` 的分区类型 |
| `bootable` | 否 | 在分区表支持时标记为可启动分区 |

## 模块

模块是 `Module(...)` 值。Board 配置将 adapter 模块与 board 模块组合；执行顺序由 `build_after`、`build_before`、`install_after` 和 `install_before` 决定。

| 字段 | 默认值 | 用途 |
| --- | --- | --- |
| `name` | 必填 | 唯一名称；有 `build` action 时也作为构建工作目录 |
| `build_after` | `[]` | 指定哪些模块必须先完成构建 |
| `build_before` | `[]` | 指定哪些模块必须在此模块之后构建 |
| `install_after` | `[]` | 指定哪些模块必须先完成安装 |
| `install_before` | `[]` | 指定哪些模块必须在此模块之后安装；适合将 board 模块插入 adapter 最终化步骤之前 |
| `requires` | `[]` | 运行前必须存在的宿主机命令 |
| `env` | `{}` | 传入构建 action 的环境变量 |
| `build` | `[]` | 构建 action 列表 |
| `install` | `[]` | 安装项；`Path` 以 `source` 方式执行脚本，`str` 直接作为 shell 命令执行 |

构建模块示例：

```python
Module(
    name="firmware",
    requires=["make"],
    env={"ARCH": "arm64", "CROSS_COMPILE": "aarch64-linux-gnu-"},
    build=[make(args="defconfig"), make()],
)
```

安装模块示例：

```python
Module(
    name="board-customization",
    install_after=["image-fstab"],
    install=[
        "echo hello",
        ctx.BOARD_DIR / "200-customization.sh",
    ],
)
```

- 有 `build` action 的模块在 `build/<board>/<module>/` 中运行，工作目录每次重建。
- 同一模块内构建 action 按顺序执行，action 写入的 `.env` 可传变量给后续构建 action。
- 构建阶段，`build_after` 和 `build_before` 约束全部满足的模块并发执行。
- install 片段在镜像生成阶段按 `install_after` 和 `install_before` 拓扑顺序运行，通过 `MODULE_DIR` 和 `BUILD_DIR` 访问构建产物。

## Install 片段

在模块的 `install` 字段中引用。`str` 值直接作为 shell 命令执行；`Path` 值以 `source` 方式执行脚本。adapter 片段放在 `adapters/<adapter>/`，board 片段放在 `boards/<board>/`，共享片段放在 `boards/`。

所有片段在同一 shell 会话中按 `install_after` 拓扑顺序运行，工作目录为 `ROOTFS`。前面片段定义的函数和变量可被后续片段使用。

| 变量 | 用途 |
| --- | --- |
| `ROOTFS` | 临时 rootfs 目录 |
| `BOARD_NAME` | 当前 board 目录名 |
| `BOARD_DIR` | 当前 board 目录绝对路径 |
| `ADAPTER_NAME` | 当前 adapter 名称 |
| `ADAPTER_DIR` | 当前 adapter 目录绝对路径 |
| `MODULE_DIR` | 当前模块的 `build/<board>/<module>/` 绝对路径 |
| `BUILD_DIR` | `build/<board>/` 的绝对路径 |
| `OUTPUT_DIR` | `outputs/<board>/` 的绝对路径 |
| `ARCH` | `config.py` 中的 `arch` 值 |

## 通用辅助项

`boards/common.py` 提供共享默认值和固件模板：

- `default_partitions()` — 标准分区布局（rootfs、boot、efi）。
- `default_images()` — 标准磁盘镜像布局（sdcard.img）。
- `firmware(arch)` — 返回包含 `opensbi`、`uboot` 和 `kernel` 工厂函数的命名空间。通用参数：`src`、`args`、`branch`、`hash`、`prebuild`、`postbuild`、`env`、`install`、`build_after`、`build_before`、`install_after`、`install_before`。此外 `uboot` 和 `kernel` 还接受 `defconfig`。`branch` 和 `hash` 透传给 `git` action；`env` 合并到默认的 module 环境变量（`CROSS_COMPILE`、`ARCH` 等）之上，可覆盖默认值。

从 `hox` 导入 API 类型，从 `actions` 导入 action 构造器：

```python
from hox import Board, ConfigContext, Module
from actions import make
```

Board 配置通过 `ctx.adapter` 加载当前 adapter。

## Actions

每个 action 模块导出 `Action` 类，`actions/__init__.py` 会为配置 re-export 常用构造器：`from actions import git, make, cp, patch, shell`。`BaseAction.use` 由模块名派生。

## 调试

输出最终配置（不运行构建和镜像）：

```sh
python main.py -b <board> -a <adapter> --skipbuild --skipimage --debug
```

在匹配的构建 action 执行前暂停并打开交互式 shell：

```sh
python main.py -b <board> -a <adapter> --debug <pattern>
```

`--debug` 的影响：

- 打印 Python DSL 求值并经 Pydantic 验证后的最终配置。
- 命中匹配的构建 action 时，在 `build/<board>/<module>/` 目录下打开 shell，环境变量包含模块 `env` 和 `.env` 文件内容。退出 shell 后继续执行。
- 命中匹配模块时，构建阶段不会并发执行，改为逐个顺序执行，便于调试。

`<pattern>` 格式为 `MODULE[:INDEX]`：

| 模式 | 含义 |
| --- | --- |
| `*` | 全部模块的构建 action |
| `kernel` | `kernel` 模块的全部构建 action |
| `kernel:0` | `kernel` 模块的第 1 个构建 action |

两部分都支持 shell 通配符，例如 `image-*`、`kernel:[0-2]`。

`--debug` 可重复以组合多个模式：

```sh
python main.py -b <board> -a <adapter> --debug 'kernel:*' --debug 'uboot:1'
```

构建 action 索引从 0 开始。
