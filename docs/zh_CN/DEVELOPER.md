# Hox SDK 开发者文档

## 核心文件

| 路径 | 说明 |
| --- | --- |
| `main.py` | 命令行入口 |
| `build_manager.py` | 构建阶段调度 |
| `image_manager.py` | 镜像阶段调度 |
| `process.py` | 统一 shell 执行与日志写入 |
| `actions/` | 构建阶段 action |
| `boards/` | 板级配置目录，通常包含 `config.jsonnet`、`genimage.cfg`、`pre/`、`post/` 和资源文件 |
| `adapters/` | 发行版适配目录，通常包含 `pre/`、`post/` 脚本 |

## 配置

`boards/<board>/config.jsonnet` 需要产出一个 JSON 对象

最小结构：

```jsonnet
{
  arch: 'riscv64',
  partitions: [],
  targets: {},
}
```

顶层字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `arch` | `string` | 目标架构，例如 `aarch64`、`riscv64` |
| `partitions` | `array<object>` | 镜像阶段创建并挂载的分区列表 |
| `targets` | `object` | 构建目标集合，键为 target 名称 |

`partitions` 常用字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `name` | `string` | 分区镜像名，不含 `.img` 后缀 |
| `mountpoint` | `string` | 挂载点，例如 `/`、`/boot` |
| `size` | `number` | 分区大小，单位为字节 |
| `mkfs` | `string` | 文件系统创建命令，例如 `mkfs.ext4` |

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

- `boards/common.jsonnet` 提供 `partitions`、`target` 以及 `opensbi`、`uboot`、`kernel` 模板函数
- 模板函数中 `prebuild` 插入到默认构建动作之前，`postbuild` 追加到默认构建动作之后

## Action

每个 action 都必须包含 `use` 字段，`BuildManager` 会加载 `actions/<use>.py` 并调用 `run()`

- action 运行目录始终是当前 target 的工作目录
- action 的有效环境变量为 `os.environ + target.env + .env`
- 如果 action 写入 `.env`，新值会从下一个 action 开始生效
- 详情见 [actions/](./actions/README.md)

## 调试

格式：

```text
TARGET[:INDEX][,...]
```

规则：

- `INDEX` 为动作下标，从 `0` 开始
- 省略 `:INDEX` 时，等价于 `:*`
- `*` 可匹配全部 target 或全部 action

示例：

- `kernel` 表示 `kernel:*`
- `*:0` 表示所有 target 的第 `0` 个 action
- `kernel:1` 表示仅在 `kernel` 的第 `1` 个 action 执行前暂停

调试 Shell 的工作目录是 `build/<board>/<target>/`，退出后构建继续执行

## 镜像阶段

流程：

1. 创建 `build/<board>/_image/` 和 `rootfs/`
2. 按 `partitions` 创建并挂载分区镜像
3. 执行 `pre`、`post` 脚本
4. 卸载分区
5. 调用 `genimage` 生成最终镜像

规则：

- 同时收集 `adapters/<adapter>/<stage>/` 和 `boards/<board>/<stage>/` 下的 `*.sh`
- 同一阶段按文件名排序执行
- 脚本通过 `source` 载入到同一个 `bash -lc` 会话中
- 脚本工作目录为 `ROOTFS`

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
