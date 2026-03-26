# goodjob — 函数调用图分析工具

静态分析源代码，构建函数调用流程图，输出为 JSON 文件。底层采用 AST 解析定位函数定义，支持多语言扩展。

---

## 安装

```bash
# 在本项目根目录安装依赖
npm install

# 全局链接（使 goodjob 命令在系统任意目录可用）
npm link
```

---

## 开发工作流

### `npm run build`

一次性编译 TypeScript + 复制 Python 脚本等资源文件到 `dist/`。

```bash
npm run build
```

> 首次使用或拉取新代码后需要先执行一次 build。

---

### `npm run copy-assets`

单独将非 TS 资源（如 `extract.py`）复制到 `dist/`，无需重新编译 TS。

```bash
npm run copy-assets
```

> 在 `npm run dev` 运行期间修改了 Python 脚本时使用。

---

### `npm run dev`

监听 `src/` 目录，文件一旦有改动立即自动重新编译，编译结果持久化到 `dist/`。

```bash
npm run dev
```

- 启动时会自动将 `src/languages/python/extract.py` 等非 TS 资源文件复制到 `dist/`。
- 保持此终端窗口运行，修改 `src/` 下任意 `.ts` 文件并保存，编译自动触发。
- 编译完成后，在**其他项目**中执行 `goodjob` 命令即可立刻使用最新代码，无需重启。
- **注意**：如果在 `dev` 运行期间修改了 `extract.py`，需要重启 `npm run dev` 或手动执行 `npm run copy-assets` 使改动生效。

---

## 使用方法

在**任意项目目录**下执行：

```bash
goodjob -entry="<入口文件路径>" -output="<输出文件路径>"
```

### 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `-entry` | 是 | 要分析的项目入口文件，相对于**当前工作目录**的路径 |
| `-output` | 是 | 分析结果 JSON 文件的输出路径，相对于**当前工作目录**的路径 |

路径支持带引号或不带引号：
```bash
goodjob -entry="./src/index.ts" -output="./output/graph.json"
goodjob -entry=./start.py -output=./output/graph.json
```

> 输出目录不存在时会自动创建。

---

## 示例

### TypeScript 项目

```bash
cd /path/to/my-ts-project
goodjob -entry="./src/index.ts" -output="./output/graph.json"
```

### Python 项目

```bash
cd /path/to/my-python-project
goodjob -entry="./start.py" -output="./output/graph.json"
```

---

## 输出格式

输出为 JSON 文件，每个函数为一个节点：

```json
[
  {
    "function_name": "main",
    "definition_file_path": "/absolute/path/to/file.ts",
    "location": "10_25",
    "childs": [
      {
        "function_name": "helper",
        "definition_file_path": "/absolute/path/to/utils.ts",
        "location": "5_12",
        "childs": null
      }
    ]
  }
]
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `function_name` | string | 函数名称 |
| `definition_file_path` | string | 函数定义所在文件的绝对路径 |
| `location` | string | 行号范围，格式为 `起始行_结束行`（1-based） |
| `childs` | array \| null | 该函数调用的子函数列表，无调用时为 `null` |

> 同一个函数被多处调用时只分析一次，避免重复和循环。

---

## 支持的语言

| 语言 | 文件扩展名 |
|------|-----------|
| TypeScript | `.ts` |
| Python | `.py` |

---

## 注意事项

1. **必须先 build**：首次使用或更新代码后，需执行 `npm run build`（或 `npm run dev`），否则 `goodjob` 命令使用的是旧的编译产物。
2. **npm link 只需执行一次**：链接后全局可用，除非重新安装 Node.js 或删除链接。
3. **路径相对于当前目录**：`-entry` 和 `-output` 路径均相对于**执行命令时所在的目录**，不是 goodjob 项目目录。
4. **循环调用保护**：同一函数对象只分析一次，不会陷入无限递归。

---

## 项目结构

```
goodjob/
├── bin/
│   └── function_graph.js   # CLI 入口，指向编译产物 dist/
├── src/
│   ├── index.ts             # 主逻辑：解析参数、调度分析
│   ├── types.ts             # 公共类型定义（GraphNode）
│   ├── graph/
│   │   ├── builder.ts       # 构建函数调用图
│   │   └── serializer.ts    # 序列化图为 JSON
│   └── languages/
│       ├── registry.ts      # 语言注册表，按文件扩展名选择分析器
│       ├── base.ts          # 分析器基类接口
│       ├── typescript/      # TypeScript 分析器
│       └── python/          # Python 分析器
├── dist/                    # 编译产物（由 tsc 生成，勿手动修改）
├── tsconfig.json
└── package.json
```
