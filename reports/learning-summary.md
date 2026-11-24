# 先修学习摘要（Learning Summary）

对照以下三份参考资料完成预习，提炼核心工程约束与可复用架构如下：

## 1. 参考工程与阶段 0 先例要点

| 来源 | 核心收获 | 对本工程（`aoitori-rw5`）的直接指导 |
| --- | --- | --- |
| **`E:\Antigravity\cafestella-rw5\`** | 1. 完整版 R18 架构：`graph.json` 节点标记 `adult: true`，`tools/` 解包→编译→图集→字体→构建→审计全流水线。<br>2. 打包与签名：`build.cjs` 通过 `aiot-toolkit 1.1.0` + `PreserveWatchAssets` 钩子阻止 PNG/JPEG 二次压缩，再用 `repack-rpk.cjs`（r1）重签名；`audit_package.py` + `rpk_signature.py` 全量校验 ZIP CRC、内外层签名、文件 SHA-256、图像尺寸及全字形覆盖。<br>3. 资源预算与性能：`24 KiB` 增量文本分片（`chunk-codec.js` 连续帧共享引用减少 RAM/GC）、`432×243` / `≤432×286` 剧情图与 `256×256` 256 色表情图集、`32 kbps Opus` 音频、防 EOF 守护与冷却重试 (`title-music.js`)、OP 时间轴同步 (`opening.js`)。 | 沿用 `build.cjs` / `repack-rpk.cjs` / `audit_package.py` 工具链与 `chunk-codec.js` / `title-music.js` / `opening.js` 架构；预算上限 25,000,000 B、条目 ≤ 4,100。 |
| **`E:\Antigravity\ginka-rw5\HANDOFF.md`** | 1. 未知格式攻坚纪律：先做全量只读探测与魔数/索引统计，输出结构化 JSON 报告与可复现脚本，不直接在原文目录写入。<br>2. 编码与环境避坑：Python 统一 `utf-8` 输出；复杂逻辑写独立 `.py`/`.cs` 脚本而非 PowerShell 内联；记录失败尝试与根因。 | 先攻克 CMVS 3.80（`.cpz`/`.ps3`/`.pb3`/`.cmv`）与 `NKA` 五种未知格式，全部解包脚本独立落盘并可复现；严格只读访问原作目录与补丁 `.bin`。 |
| **`D:\codex\移植项目\senren-rw5\源码\`** | 1. 阅读器状态机：`engine.js`（`create`/`checkpoint`/`restore`/`locate`/`advance`/`choose`/`skipChapter`/`previous`，24 步回退历史、30 槽存档、章节预览隔离 `progression: 'chapter'`）。<br>2. 关键硬坑规避：字体子集化必须设置 **`desubroutinize=True` + `hinting=False`**（消除手表 FreeType `callgsubr` 渲染空框）；条目数须 **≤ 4,100**（实测 4,177 触发 `rpkpackage -19`）；故事块控制在 ≤ 28 KiB。 | 复用 `engine.js`、`auto-reader.js`、30 槽存档与 `desubroutinize=True, hinting=False` 字体管线，并按青鸟需求扩展显式 `screenState`、`adultEnabled` 开关与幂等槽位立绘状态机。 |

## 2. 本轮关键差异与攻坚目标

- **引擎完全不同**：原作为 **CMVS `cmvs32[ver.3.80]` + `ps3[ver.1.00]`**（非 KiriKiri XP3/PSB），需独立实现 `.cpz`、`.ps3`（`PSA0`）、`.pb3`、`.cmv` 及 R18 补丁 `.nka`（`NKA\0`）的解析与验证。
- **核心硬性约束**：
  1. R18 补丁以 `AoiToriR18Patchv1.04.bin`（NKA）为准，与 `data/` 现况逐字节比对并输出 `reports/r18-merge.json`。
  2. 显式 `screenState`（`TITLE` / `TITLE_SUB` / `GAME`）音频状态机，严禁标题曲串入游戏正文/内菜单。
  3. 标题画面随通关进度切换背景与解锁菜单项，立绘采用「角色槽位」主键的幂等状态机并对照 `stand` / `up` 切分规则。
