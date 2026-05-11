# Hox SDK 开发者文档

## 核心文件

| 路径 | 说明 |
| --- | --- |
| `main.py` | 命令行入口 |
| `build_manager.py` | 构建阶段调度 |
| `image_manager.py` | 镜像阶段调度 |
| `process.py` | 统一 shell 执行与日志写入 |
| `actions/` | 构建阶段 action |
| `boards/` | 板级配置目录，通常包含 `config.jsonnet`、`pre/`、`post/` 和资源文件 |
| `adapters/` | 发行版适配目录，通常包含 `pre/`、`post/` 脚本 |

## 配置

`boards/<board>/config.jsonnet` 需要产出一个 JSON 对象

最小结构：

```jsonnet
{
  arch: 'riscv64',
  partitions: [],
  images: [],
  targets: {},
}
```

顶层字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `arch` | `string` | 目标架构，例如 `aarch64`、`riscv64` |
| `partitions` | `array<object>` | 需要创建、格式化并挂载的分区镜像定义列表 |
| `images` | `array<object>` | 最终磁盘镜像配置列表 |
| `targets` | `object` | 构建目标集合，键为 target 名称 |

顶层 `partitions` 条目字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `name` | `string` | 分区镜像文件名，例如 `rootfs.img` |
| `size` | `number` | 分区大小，单位为扇区 |
| `mkfs` | `string` | 文件系统创建命令 |
| `mountpoint` | `string` | 挂载点；会先创建并挂载该镜像，再安装 rootfs |

`images` 条目字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `name` | `string` | 最终磁盘镜像文件名，例如 `sdcard.img` |
| `table` | `string` | 分区表类型，例如 `gpt` 或 `dos` |
| `partitions` | `array<object>` | 按最终磁盘分区顺序排列的分区引用列表 |

`images[].partitions` 条目字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `name` | `string` | 镜像工作目录中的分区镜像文件名 |
| `start` | `number` | 分区起始位置，单位为扇区 |
| `size` | `number` | 分区镜像大小，单位为扇区；省略时按文件大小自动探测 |
| `type` | `string` | 传给 `sfdisk` 的分区类型，例如 GPT type UUID |

### Target

| 字段 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `requires` | `array<string>` | `[]` | 执行前检查的宿主机命令 |
| `depends` | `array<string>` | `[]` | 依赖的其他 target 名称 |
| `env` | `object` | `{}` | 传递给 action 的环境变量 |
| `actions` | `array<object>` | `[]` | 按顺序执行的动作列表 |
| `result` | `array<string>` | `[]` | 构建完成后从工作目录中收集并移动到 `outputs/<board>/` 的 glob |

示例：

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
        { use: 'git', src: 'https://github.com/torvalds/linux' },
        { use: 'make', args: 'defconfig' },
        { use: 'make' },
      ],
      result: ['arch/*/boot/Image.gz'],
    },
  },
}
```

规则：

- 默认情况下，target 按依赖关系并发调度
- 开启 `--debug` 后，target 会逐个等待，便于交互调试
- 同一 target 内的 `actions` 严格按顺序执行
- 每个 target 的工作目录为 `build/<board>/<target>/`，每次构建前都会被重新创建
- 每次 action 执行前都会读取 `.env`，并覆盖同名的 `target.env` 变量
- `result` 匹配到的文件或目录会移动到 `outputs/<board>/` 根目录
- `BDIR` 是当前板级目录的绝对路径

辅助项：

- `boards/common.jsonnet` 提供 `partitions`、`images`、`target` 以及 `opensbi`、`uboot`、`kernel` 模板函数
- 模板函数中 `prebuild` 插入到默认构建动作之前，`postbuild` 追加到默认构建动作之后

## Action

每个 action 都必须包含 `use` 字段，`BuildManager` 会加载 `actions/<use>.py` 并调用 `run()`

- action 运行目录始终是当前 target 的工作目录
- action 的有效环境变量为 `os.environ + target.env + .env`
- 如果 action 写入 `.env`，新值会从下一个 action 开始生效
- 详情见 [actions/](./actions/README.md)

## 调试

`--debug` 接受以下格式的断点匹配：

```text
TARGET[:INDEX][,...]
```

- `*` 匹配全部 target 或 action
- `kernel` 表示 `kernel:*`
- `*:1` 匹配所有 target 的第 `1` 个 action
- `kernel:*` 匹配 `kernel` 的所有 action
- `kernel:1` 匹配 `kernel` 的第 `1` 个 action

`--debug` 不带值时等价于 `--debug '*'`。使用 `--skipbuild --skipimage --debug` 可以只输出解析后的 Jsonnet 配置。

## 镜像阶段

流程：

1. 创建 `build/<board>/_image/` 和 `rootfs/`
2. 按顶层 `partitions` 中带 `mountpoint` 的条目创建并挂载分区镜像
3. 执行 `pre`、`post` 脚本
4. 卸载分区
5. 按 `images` 使用 `sfdisk` 写出最终磁盘镜像

规则：

- 同时收集 `adapters/<adapter>/<stage>/` 和 `boards/<board>/<stage>/` 下的 `*.sh`
- 同一阶段按文件名排序执行
- 脚本通过 `source` 载入到同一个 `bash -lc` 会话中
- 脚本工作目录为 `ROOTFS`
- `images[].name` 作为最终磁盘镜像输出名
- 外部镜像不要定义在顶层 `partitions` 中；在 `images[].partitions[]` 中直接引用其文件名；`size` 可显式提供，也可省略后按文件大小自动探测

脚本环境变量：

| 变量 | 说明 |
| --- | --- |
| `ROOTFS` | 临时根文件系统目录 |
| `BOARD_NAME` | 当前板级目录名 |
| `BOARD_DIR` | 当前板级目录绝对路径 |
| `ADAPTER_NAME` | 当前 adapter 名称 |
| `ADAPTER_DIR` | 当前 adapter 目录绝对路径 |
| `BUILD_DIR` | 当前 board 的构建目录绝对路径 |
| `OUTPUT_DIR` | 当前 board 的输出目录绝对路径 |
| `FIRMWARE_DIR` | 当前实现中等同于 `OUTPUT_DIR` |
| `ARCH` | 目标架构 |
| `DESKTOP` | 命令行传入的桌面配置名 |
