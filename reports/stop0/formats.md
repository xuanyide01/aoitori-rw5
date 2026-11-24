# Stop 0 · 《アオイトリ / AOI TORI》五种格式与汉化数据源说明

## 1. `.cpz`（`CPZ7` 归档）
- **文件分布**：`data/pack/` 下 7 个包，移植纳入 5 个：`ps.cpz`（3 条）、`bg.cpz`（128 条）、`stand.cpz`（5,082 条）、`up.cpz`（5,082 条）、`balloon.cpz`（9,044 条）；`voice.cpz` / `voice2.cpz` 按规格舍弃。
- **结构与加密**：魔数 `CPZ7`，索引含目录表与条目表（经 Huffman 压缩密钥 + 旋转置换 + `start.ps3` 中的 4 组 `ArchiveKey` 解密）；采用 `Aoi Tori` `CmvsScheme`（`Version=7`, `Md5Variant=Aoi`, `DecoderFactor=443871637`, `EntryInitKey=659080094`, `EntrySubKey=1547298939`）。
- **解包工具**：`GARbro-Mod` (`GameRes.Formats.Purple.CpzOpener`) 完整支持，提取时自动对 `PS2A` 解包、对 `PB3B` 执行尾部 47 字节密钥解密。

## 2. `.ps3`（`PS2A` 脚本字节码）
- **文件分布**：`data/code/*.ps3` 共 86 个（Steam 官英 + R18 v1.04 补丁，共 45,383 条英文字符串，0 条中文）。
- **中文源（`Longinus.dat`）**：天之圣杯汉化组外挂资源包 `Longinus.dat`（321,063,702 B，魔数 `Longinus`，flags `(1,4,0,1)`，共 137 条），索引为 `(uint32 hash, uint32 size, uint32 offset)`，哈希为 `BKDR(name.upper().encode('utf-16le'), mul=131) & 0x7FFFFFFF`。内含 **85 个明文 GBK 中文 `.ps3` 脚本**（除无对白的 `intcode.ps3` 外全覆盖）及 **52 张原始 BGRA 汉化 UI/CG 图**。
- **二进制结构（48 B 头 `PS3_HDR`）**：`magic='PS2A'`、`hdrSize=0x30`、`labelCount`（跳转标签表 `4 * labelCount` 字节）、`codeBlockSize`、`unBlockSize`、`textBlockSize`、`dataCompressSize`、`dataDecompressSize`。
- **字节码要点**：压入字符串指令为 `01 02 20 01 <uint32 text_rva> 0F 02 30 04`；正文中对白按 `[文本, 语音ogg/空, 说话人/空]` 三元组出现；系统指令 `0x2210`/`0x2370` 为选项分支，`0x2080` 打开新脚本；全 86 个脚本共提取 **70,988 条简体中文文本**，含 9 个 `snh*.ps3` 专属成人剧本。

## 3. `.pb3`（`PB3B` 图像容器与立绘切分）
- **文件分布**：`data/image/`（`chip/` 193、`event/` 1,614［含 `h_*` 1,107］、`update/` 1,702）及 `bg.cpz`/`stand.cpz`/`up.cpz`/`balloon.cpz` 内；另 `Longinus.dat` 含 52 张汉化 UI/CG 原尺寸 BGRA 覆盖。
- **容器与子类型**：魔数 `PB3B`，支持 `Type 1`（16×16 块 LZSS）、`Type 2/3`（`JBP1` DCT/Huffman + RLE Alpha，如 `bg010a.pb3` 2048×1024 24bpp）、`Type 5`（4 通道差分 LZSS，用于底图如 `st-mr_a101.pb3` 680×1536 32bpp）、`Type 6/8`（`0x34..0x53` 经 `NameKeyV6` 异或得到底图名，随后叠加 8×8 变更块，用于差分表情/服装如 `st-mr_a102.pb3`）。
- **立绘组切分规则**：`stand.cpz`（`st-*`，680×1536）为全身立绘，`up.cpz`（`up-*`，784×1280）为半身特写，`balloon.cpz`（`fk1-*`/`fk2-*`，512×512）为对话框头像；`intcode.ps3` 集中登记前缀 `st-`/`up-`/`fk1-`/`fk2-` 与角色代码及姿态/表情编号。

## 4. `.cmv`（`CMV6` / `CMV9` 影片与 `JBPD` 帧）
- **结构**：44 B 头部（`CMV6`/`CMV9`、`resSecOffset`、`fileSize`、`maxSequence`、`fps`、`width`、`height`、`bpp`），后接 `maxSequence + 1` 条 20 B 索引 `(seq, cmpSize, orgSize, resType, offset)`，其中 `resType=0` 为内嵌 `OggS` 音频，`resType=2` 为 `JBPD` 图像帧。
- **`op.cmv` 实测**：`CMV6`，1280×720 24bpp @ 24 fps，2,915 帧（索引 0..2914，约 121.46 s）+ 索引 2915 内嵌 `OggS` OP 音轨（1,909,836 B）。
- **`JBPD` 解码**：在 `JBP1` 基础上于 `0x2c` 插入 `uint32 sectorMask`（1280×720 为 `0x7fff`，3×5 共 15 个 `256×256`/`256×208` 区块），`0xc0` 起为 `quant_y`/`quant_c`，`0x140` 起为 `[rows, cols, nSectors, 0]` 及各区块 `(bh, bw)` 表，之后为 DC/AC 哈夫曼比特流。实测 `test_jbpd_full.cs` 成功还原 1280×720 清晰帧。
- **`data/imgvideo/*.cmv`（27 个）**：`CMV9` 动态背景/特效（含 `sectorMask` 局部区块更新，如 `bg070a.cmv` 1536×1280 @ 15 fps 45 帧）。

## 5. `.nka`（`NKA\0` R18 补丁归档）
- **结构**：12 B 头部（`b'NKA\x00'`, `version=1`, `count=18362`），后接明文条目表：`name_len + utf8 name + (f1,f2,f3,f4) + h1(32B目标SHA256) + h2(32B原文件SHA256) + uint64 offset + uint64 size`。
- **压缩与差分类型**：
  - `f=(3,0,2,0)`（2,995 条）：`zstd` 整文件替换（如 `omake.ps3`、`balloon.cpz`、`stand.cpz`、`up.cpz`、`op.cmv`、`image/event/*`）。
  - `f=(3,0,2,1)`（473 条）：`zstd` 压缩的 `BSDIFF40` 二进制差分补丁（如 `code/*.ps3`）。
  - `f=(0,0,0,4)`（14,894 条）：删除标记或已合并入 `.cpz` 的散包占位（如 `code/sn215.ps3`、`image/chip/thanks.pb3`）。
- **合并校验**：对磁盘 `data/` 逐项校验 SHA-256，86/86 `code/*.ps3`、3,378/3,378 `image/*`、3 个 `.cpz` 与 `op.cmv` 已全部精确匹配 `h1`（补丁后版本）。
