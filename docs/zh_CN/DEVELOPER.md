# Hox SDK 开发者文档

## 目的

本文说明如何添加或维护 SDK 的板级配置、构建目标、action 和镜像脚本。

## 仓库结构

| 路径 | 用途 |
| --- | --- |
| `main.py` | SDK 命令入口 |
| `boards/` | 板级定义和板级资源 |
| `boards/common.jsonnet` | 通用分区、镜像和构建目标的 Jsonnet 辅助项 |
| `adapters/` | 发行版 rootfs 和镜像定制脚本 |
| `actions/` | 可复用构建 action |
| `docs/zh_CN/actions/` | action 字段参考文档 |
| `build/` | 生成的工作目录 |
| `outputs/` | 生成的构建产物和磁盘镜像 |
| `logs/` | 命令日志 |

SDK 开发者主要会接触这些格式：

- Jsonnet：板级配置
- Shell 脚本：镜像定制
- Python：SDK 框架 action 和命令编排

## 添加或更新板级配置

板级配置位于 `boards/<board>/`，其中 `<board>` 是传给 `python main.py -b` 的值。

必需文件：

| 路径 | 用途 |
| --- | --- |
| `boards/<board>/config.jsonnet` | 板级架构、构建目标、分区布局和最终镜像布局 |

可选板级目录：

| 路径 | 用途 |
| --- | --- |
| `boards/<board>/pre/` | 镜像 pre 阶段运行的板级脚本 |
| `boards/<board>/post/` | 镜像 post 阶段运行的板级脚本 |
| 其他板级本地路径 | 配置或脚本引用的补丁、overlay、固件或其他板级资源 |

`main.py` 会把 `BDIR` 作为当前板级目录的绝对路径传给 Jsonnet。配置需要引用板级本地文件时可以使用它：

```jsonnet
local BDIR = std.extVar('BDIR');
```

最小板级配置：

```jsonnet
{
  arch: 'riscv64',
  partitions: [],
  images: [],
  targets: {},
}
```

## 板级配置字段

顶层字段：

| 字段 | 必需 | 用途 |
| --- | --- | --- |
| `arch` | 生成镜像时必需 | 目标架构，会作为 `ARCH` 传给镜像脚本 |
| `partitions` | 否 | 脚本运行前需要创建、格式化并挂载的分区镜像 |
| `images` | 否 | 需要写出的最终磁盘镜像 |
| `targets` | 否 | 构建目标集合，键为 target 名称 |

`partitions` 字段中的条目：

| 字段 | 必需 | 用途 |
| --- | --- | --- |
| `name` | 是 | 分区镜像文件名 |
| `size` | 是 | 分区大小，单位为 512 字节扇区 |
| `mkfs` | 是 | 文件系统命令，例如 `mkfs.ext4` |
| `mountpoint` | 是 | 临时 rootfs 内的挂载点 |

`images` 字段中的条目：

| 字段 | 必需 | 用途 |
| --- | --- | --- |
| `name` | 是 | `outputs/<board>/` 下的最终镜像文件名 |
| `table` | 否 | 分区表类型：`gpt` 或 `dos`；默认是 `gpt` |
| `partitions` | 是 | 最终镜像中的分区引用列表，顺序即分区顺序 |

`images[].partitions` 字段中的条目：

| 字段 | 必需 | 用途 |
| --- | --- | --- |
| `name` | 是 | 分区镜像文件名 |
| `start` | 是 | 起始偏移，单位为 512 字节扇区 |
| `size` | 否 | 分区大小，单位为扇区；省略时根据分区镜像文件大小推断 |
| `type` | 否 | 传给 `sfdisk` 的分区类型 |
| `bootable` | 否 | 在分区表支持时标记为可启动分区 |

## `targets` 字段

每个 target 描述一个构建单元。

| 字段 | 默认值 | 用途 |
| --- | --- | --- |
| `requires` | `[]` | target 运行前必须存在的宿主机命令 |
| `depends` | `[]` | 必须先完成的其他 target |
| `env` | `{}` | 传给 action 的环境变量 |
| `actions` | `[]` | 按顺序执行的构建 action 列表 |
| `result` | `[]` | 从 target 工作目录移动到 `outputs/<board>/` 的 glob 匹配规则 |

target 示例：

```jsonnet
{
  targets: {
    kernel: {
      requires: ['make'],
      env: {
        ARCH: 'arm64',
        CROSS_COMPILE: 'aarch64-linux-gnu-',
      },
      actions: [
        { use: 'make', args: 'defconfig' },
        { use: 'make' },
      ],
      result: ['arch/*/boot/Image.gz'],
    },
  },
}
```

target 规则：

- target 在 `build/<board>/<target>/` 中运行。
- 每次运行 target 前都会重新创建对应工作目录。
- target 依赖通过 `depends` 声明。
- 同一 target 内的 action 按顺序运行。
- `result` 匹配到的文件会移动到 `outputs/<board>/`。
- action 写入的 `.env` 文件可以把变量传给同一 target 后续 action。

## 通用辅助项

如果适合当前板级配置，优先使用 `boards/common.jsonnet`。

可用辅助项：

| 辅助项 | 用途 |
| --- | --- |
| `partitions` | 通用 `rootfs.img`、`boot.img` 和 `efi.img` 分区定义 |
| `images` | 通用 `sdcard.img` 镜像定义 |
| `target(...)` | 使用共享架构环境变量创建 target |
| `opensbi(...)` | 通用 OpenSBI 构建 target 模板 |
| `uboot(...)` | 通用 U-Boot 构建 target 模板 |
| `kernel(...)` | 通用 Linux kernel 构建 target 模板 |

模板辅助项支持通过 `prebuild` 和 `postbuild` action 列表加入板级定制步骤。

## Actions

action 通过 `use` 字段选择。

action 实现位于 `actions/`。action 字段文档位于 `docs/zh_CN/actions/`。

添加 target 时，优先使用已有 action。只有确实需要时才新增 action；新增时需要添加 `actions/<name>.py`，并在 `docs/zh_CN/actions/<name>.md` 中记录字段说明。

## 镜像脚本

镜像脚本用于定制临时 rootfs 和最终镜像输入。

脚本位置：

| 路径 | 用途 |
| --- | --- |
| `adapters/<adapter>/pre/*.sh` | adapter pre 阶段脚本 |
| `boards/<board>/pre/*.sh` | board pre 阶段脚本 |
| `adapters/<adapter>/post/*.sh` | adapter post 阶段脚本 |
| `boards/<board>/post/*.sh` | board post 阶段脚本 |

脚本规则：

- `pre` 先于 `post` 运行。
- adapter 脚本和 board 脚本都会被包含。
- 同一阶段内脚本按文件名顺序运行。
- 脚本在同一个 shell 会话中运行，因此前面脚本定义的函数可被后续脚本使用。
- 脚本工作目录是 `ROOTFS`。

脚本环境变量：

| 变量 | 用途 |
| --- | --- |
| `ROOTFS` | 临时 rootfs 目录 |
| `BOARD_NAME` | 当前 board 目录名 |
| `BOARD_DIR` | 当前 board 目录绝对路径 |
| `ADAPTER_NAME` | 当前 adapter 名称 |
| `ADAPTER_DIR` | 当前 adapter 目录绝对路径 |
| `BUILD_DIR` | `build/<board>/` 的绝对路径 |
| `OUTPUT_DIR` | `outputs/<board>/` 的绝对路径 |
| `FIRMWARE_DIR` | 与 `OUTPUT_DIR` 相同 |
| `ARCH` | `config.jsonnet` 中的 board 架构 |
| `DESKTOP` | 通过 `--desktop` 传入的值 |

## 调试

输出 Jsonnet 求值后的最终 JSON 配置，不运行构建阶段和镜像阶段：

```sh
python main.py -b <board> -a <adapter> --skipbuild --skipimage --debug
```

在匹配的 action 前打开调试 shell：

```sh
python main.py -b <board> -a <adapter> --debug <target[:index]>
```

匹配模式：

| 模式 | 含义 |
| --- | --- |
| `*` | 全部 target 和 action |
| `kernel` | `kernel` 中的全部 action |
| `kernel:0` | `kernel` 中的第一个 action |
| `*:1` | 每个 target 中的第二个 action |

action 索引从 0 开始。

## 验证

修改 SDK 配置后可使用这些检查：

```sh
python main.py --help

# 检查 `boards/<board>/config.jsonnet` 生成的最终 JSON 配置。
python main.py -b <board> -a <adapter> --skipbuild --skipimage --debug
```
