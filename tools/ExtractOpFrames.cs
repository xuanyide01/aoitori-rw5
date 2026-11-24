using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;

class ExtractOpFrames {
    static readonly byte[] ZigzagOrder = new byte[64] {
         1,  8, 16,  9,  2,  3, 10, 17,
        24, 32, 25, 18, 11,  4,  5, 12,
        19, 26, 33, 40, 48, 41, 34, 27,
        20, 13,  6,  7, 14, 21, 28, 35,
        42, 49, 56, 57, 50, 43, 36, 29,
        22, 15, 23, 30, 37, 44, 51, 58,
        59, 52, 45, 38, 31, 39, 46, 53,
        60, 61, 54, 47, 55, 62, 63,  0
    };

    static readonly byte[] YccClampTable = Enumerable.Repeat((byte)0, 0x100)
        .Concat(Enumerable.Range(0, 0x100).Select(x => (byte)x))
        .Concat(Enumerable.Repeat((byte)0xFF, 0x100)).ToArray();

    class JBitStream {
        byte[] m_input;
        int m_pos, m_end, m_bits, m_cached_bits;
        public JBitStream(byte[] input, int offset, int length) {
            m_input = input; m_pos = offset; m_end = offset + length;
        }
        static int ReverseByteBits(int x) {
            x = (x & 0xAA) >> 1 | (x & 0x55) << 1;
            x = (x & 0xCC) >> 2 | (x & 0x33) << 2;
            return (x >> 4 | x << 4) & 0xFF;
        }
        public int GetBits(int count) {
            while (m_cached_bits < count) {
                if (m_pos >= m_end) throw new EndOfStreamException();
                m_bits = (m_bits << 8) | ReverseByteBits(m_input[m_pos++]);
                m_cached_bits += 8;
            }
            int mask = (1 << count) - 1;
            m_cached_bits -= count;
            return (m_bits >> m_cached_bits) & mask;
        }
        public int GetNextBit() { return GetBits(1); }
    }

    class HuffmanTree {
        public byte[] Base;
        int[] Nodes = new int[0x400];
        int Root;
        public int LeafCount { get { return Base.Length; } }
        const uint MaxFreq = 2100000000u;
        public HuffmanTree(byte[] input, uint[] freq) {
            Base = input;
            int depth = Base.Length;
            for (;;) {
                int l = -1; uint min = MaxFreq - 1;
                for (int i = 0; i < depth; ++i) if (freq[i] < min) { min = freq[i]; l = i; }
                int r = -1; min = MaxFreq - 1;
                for (int i = 0; i < depth; ++i) if (i != l && freq[i] < min) { min = freq[i]; r = i; }
                if (l < 0 || r < 0) break;
                Nodes[depth] = l;
                Nodes[depth + 0x200] = r;
                freq[depth++] = freq[l] + freq[r];
                freq[l] = MaxFreq;
                freq[r] = MaxFreq;
            }
            Root = depth - 1;
        }
        public int Read(JBitStream bits) {
            int v = Root;
            while (v >= LeafCount) v = Nodes[v + (bits.GetNextBit() << 9)];
            return v;
        }
    }

    static void Dct(short[] dct_table, short[] quant) {
        int a, b, c, d, w, x, y, z, s, t, u, v, n;
        int p = 0, q = 0;
        for (int i = 0; i < 8; ++i) {
            if (dct_table[p+0x08] == 0 && dct_table[p+0x10] == 0 &&
                dct_table[p+0x18] == 0 && dct_table[p+0x20] == 0 &&
                dct_table[p+0x28] == 0 && dct_table[p+0x30] == 0 &&
                dct_table[p+0x38] == 0) {
                dct_table[p] = dct_table[p+0x08] = dct_table[p+0x10] = dct_table[p+0x18] =
                dct_table[p+0x20] = dct_table[p+0x28] = dct_table[p+0x30] = dct_table[p+0x38] = (short)(dct_table[p] * quant[q]);
            } else {
                c = quant[q+0x10] * dct_table[p+0x10];
                d = quant[q+0x30] * dct_table[p+0x30];
                x = ((c + d) * 35467) >> 16;
                c = ((c * 50159) >> 16) + x;
                d = ((d * -121094) >> 16) + x;
                a = dct_table[p+0x00] * quant[q+0x00];
                b = dct_table[p+0x20] * quant[q+0x20];
                w = a + b + c; x = a + b - c; y = a - b + d; z = a - b - d;
                c = dct_table[p+0x38] * quant[q+0x38];
                d = dct_table[p+0x28] * quant[q+0x28];
                a = dct_table[p+0x18] * quant[q+0x18];
                b = dct_table[p+0x08] * quant[q+0x08];
                n = ((a + b + c + d) * 77062) >> 16;
                u = n + ((c * 19571) >> 16) + (((c + a) * -128553) >> 16) + (((c + b) * -58980) >> 16);
                v = n + ((d * 134553) >> 16) + (((d + b) * -25570) >> 16) + (((d + a) * -167963) >> 16);
                t = n + ((b * 98390) >> 16) + (((d + b) * -25570) >> 16) + (((c + b) * -58980) >> 16);
                s = n + ((a * 201373) >> 16) + (((c + a) * -128553) >> 16) + (((d + a) * -167963) >> 16);
                dct_table[p] = (short)(w + t); dct_table[p+0x38] = (short)(w - t);
                dct_table[p+0x08] = (short)(y + s); dct_table[p+0x30] = (short)(y - s);
                dct_table[p+0x10] = (short)(z + v); dct_table[p+0x28] = (short)(z - v);
                dct_table[p+0x18] = (short)(x + u); dct_table[p+0x20] = (short)(x - u);
            }
            p++; q++;
        }
        p = 0;
        for (int i = 0; i < 8; ++i) {
            a = dct_table[p]; c = dct_table[p+2]; b = dct_table[p+4]; d = dct_table[p+6];
            x = ((c + d) * 35467) >> 16;
            c = ((c * 50159) >> 16) + x;
            d = ((d * -121094) >> 16) + x;
            w = a + b + c; x = a + b - c; y = a - b + d; z = a - b - d;
            d = dct_table[p+5]; b = dct_table[p+1]; c = dct_table[p+7]; a = dct_table[p+3];
            n = ((a + b + c + d) * 77062) >> 16;
            s = n + ((a * 201373) >> 16) + (((a + c) * -128553) >> 16) + (((a + d) * -167963) >> 16);
            t = n + ((b * 98390) >> 16) + (((b + c) * -58980) >> 16) + (((b + d) * -25570) >> 16);
            u = n + ((c * 19571) >> 16) + (((b + c) * -58980) >> 16) + (((a + c) * -128553) >> 16);
            v = n + ((d * 134553) >> 16) + (((b + d) * -25570) >> 16) + (((a + d) * -167963) >> 16);
            dct_table[p  ] = (short)((w + t) >> 3); dct_table[p+7] = (short)((w - t) >> 3);
            dct_table[p+1] = (short)((y + s) >> 3); dct_table[p+6] = (short)((y - s) >> 3);
            dct_table[p+2] = (short)((z + v) >> 3); dct_table[p+5] = (short)((z - v) >> 3);
            dct_table[p+3] = (short)((x + u) >> 3); dct_table[p+4] = (short)((x - u) >> 3);
            p += 8;
        }
    }

    static void Ycc2Rgb(byte[] output, int stride, int dc, int ac, short[] dct_y, short[] dct_cb, short[] dct_cr, int cbcr_src) {
        int y_src = 0;
        for (int y = 0; y < 4; ++y) {
            for (int x = 0; x < 4; ++x) {
                var cb = dct_cb[cbcr_src];
                var cr = dct_cr[cbcr_src];
                var r = ((cr * 0x166F0) >> 16);
                var g = ((cb * 0x5810) >> 16) + ((cr * 0xB6C0) >> 16);
                var b = ((cb * 0x1C590) >> 16);
                var c0 = dct_y[y_src] + 0x180;
                var c1 = dct_y[y_src + 1] + 0x180;
                var c8 = dct_y[y_src + 8] + 0x180;
                var c9 = dct_y[y_src + 9] + 0x180;

                output[dc]              = YccClampTable[c0 + b];
                output[ac + 1 - stride] = YccClampTable[c0 - g];
                output[ac + 2 - stride] = YccClampTable[c0 + r];
                output[ac + 4 - stride] = YccClampTable[c1 + b];
                output[ac + 5 - stride] = YccClampTable[c1 - g];
                output[ac + 6 - stride] = YccClampTable[c1 + r];
                output[ac]              = YccClampTable[c8 + b];
                output[ac + 1]          = YccClampTable[c8 - g];
                output[ac + 2]          = YccClampTable[c8 + r];
                output[ac + 4]          = YccClampTable[c9 + b];
                output[ac + 5]          = YccClampTable[c9 - g];
                output[ac + 6]          = YccClampTable[c9 + r];
                y_src += 2;
                dc += 8;
                ac += 8;
                cbcr_src++;
            }
            dc += stride * 2 - 32;
            ac += stride * 2 - 32;
            y_src += 8;
            cbcr_src += 4;
        }
    }

    static void DecodeJbpdIntoBuffer(byte[] input, byte[] canvas, int width, int height) {
        int dataPos = BitConverter.ToInt32(input, 4);
        ushort flags = BitConverter.ToUInt16(input, 8);
        bool hasMask = (flags & 0x1000) != 0;
        int dcLen = BitConverter.ToInt32(input, 0x1C);
        int acLen = BitConverter.ToInt32(input, 0x20);
        uint sectorMask = BitConverter.ToUInt32(input, dataPos);

        var freq = new uint[0x20];
        Buffer.BlockCopy(input, dataPos + 4, freq, 0, 0x40);
        var treeData = new byte[0x10];
        int treePos = dataPos + 4 + 0x80;
        for (int i = 0; i < 0x10; ++i) treeData[i] = (byte)(input[treePos + i] + 1);
        var treeDc = new HuffmanTree(treeData, freq);
        Buffer.BlockCopy(input, dataPos + 4 + 0x40, freq, 0, 0x40);
        var treeAc = new HuffmanTree(treeData, freq);

        int quantPos = treePos + 0x10;
        var quantY = new short[0x40];
        var quantC = new short[0x40];
        for (int i = 0; i < 0x40; ++i) {
            quantY[i] = input[quantPos + i];
            quantC[i] = input[quantPos + 0x40 + i];
        }

        int gridPos = quantPos + 0x80;
        int cols = input[gridPos + 1];
        int nSectors = input[gridPos + 2];
        int baseBitsOffset = (gridPos + 4 + nSectors * 2 + 3) & ~3;

        int totalGridBlocks = 0;
        int[] sectorBitStart = new int[nSectors];
        for (int s = 0; s < nSectors; ++s) {
            sectorBitStart[s] = totalGridBlocks;
            totalGridBlocks += input[gridPos + 4 + s * 2] * input[gridPos + 4 + s * 2 + 1];
        }
        int maskBytes = hasMask ? (((totalGridBlocks + 31) / 32) * 4) : 0;
        int maskOffset = baseBitsOffset;
        int bitsOffset = baseBitsOffset + maskBytes;
        if (totalGridBlocks == 0) return;

        var bitsDc = new JBitStream(input, bitsOffset, dcLen);
        var bitsAc = new JBitStream(input, bitsOffset + dcLen, acLen);

        // JBPD always packs DC and AC streams across ALL totalGridBlocks in sector scan order,
        // even when sectorMask or the 1-bit block mask omits applying unchanged blocks to canvas.
        var blocks = new short[totalGridBlocks, 6];
        uint prevV = 0;
        for (int i = 0; i < totalGridBlocks; ++i)
        for (int j = 0; j < 6; ++j) {
            int bc = treeDc.Read(bitsDc);
            uint v = (uint)bitsDc.GetBits(bc);
            if (v < (1u << (bc - 1))) v -= (1u << bc) - 1;
            prevV += v;
            blocks[i, j] = (short)prevV;
        }

        int fullStride = width * 4;
        var dctTable = new short[6][];
        for (int i = 0; i < 6; ++i) dctTable[i] = new short[64];

        int blkIdx = 0;
        for (int s = 0; s < nSectors; ++s) {
            bool sectorActive = (sectorMask & (1u << s)) != 0;
            int sr = s / cols;
            int sc = s % cols;
            int bh = input[gridPos + 4 + s * 2];
            int bw = input[gridPos + 4 + s * 2 + 1];
            int secW = bw * 16;
            int secH = bh * 16;
            int secStride = secW * 4;
            int dstX = sc * 256;
            int dstY = sr * 256;

            byte[] secOut = null;
            if (sectorActive) {
                secOut = new byte[secStride * secH];
                if (hasMask) {
                    for (int row = 0; row < secH; ++row) {
                        if (dstY + row >= height) break;
                        int copyBytes = Math.Min(secStride, (width - dstX) * 4);
                        Buffer.BlockCopy(canvas, (dstY + row) * fullStride + dstX * 4, secOut, row * secStride, copyBytes);
                    }
                }
            }

            int sBit = sectorBitStart[s];
            for (int y = 0; y < bh; ++y) {
                int dst1 = y * secStride * 16;
                int dst2 = dst1 + secStride * 9;
                for (int x = 0; x < bw; ++x) {
                    for (int j = 0; j < 6; ++j) Array.Clear(dctTable[j], 0, 64);
                    for (int n = 0; n < 6; ++n) {
                        dctTable[n][0] = blocks[blkIdx, n];
                        for (int i = 0; i < 63;) {
                            int bc = treeAc.Read(bitsAc);
                            if (15 == bc) break;
                            if (0 == bc) {
                                int nodeIdx = 0;
                                while (0 != bitsAc.GetNextBit()) nodeIdx++;
                                i += treeAc.Base[nodeIdx];
                            } else {
                                uint v = (uint)bitsAc.GetBits(bc);
                                if (v < (1u << (bc - 1))) v -= (1u << bc) - 1;
                                dctTable[n][ZigzagOrder[i]] = (short)v;
                                ++i;
                            }
                        }
                    }
                    blkIdx++;

                    int bi = sBit + y * bw + x;
                    bool applyBlock = sectorActive && (!hasMask || ((input[maskOffset + (bi >> 3)] & (0x80 >> (bi & 7))) == 0));
                    if (applyBlock) {
                        Dct(dctTable[0], quantY);
                        Dct(dctTable[1], quantY);
                        Dct(dctTable[2], quantY);
                        Dct(dctTable[3], quantY);
                        Dct(dctTable[4], quantC);
                        Dct(dctTable[5], quantC);
                        Ycc2Rgb(secOut, secStride, dst1, dst1 + secStride, dctTable[0], dctTable[4], dctTable[5], 0);
                        Ycc2Rgb(secOut, secStride, dst1 + 32, dst1 + secStride + 32, dctTable[1], dctTable[4], dctTable[5], 4);
                        Ycc2Rgb(secOut, secStride, dst2 - secStride, dst2, dctTable[2], dctTable[4], dctTable[5], 32);
                        Ycc2Rgb(secOut, secStride, dst2 - secStride + 32, dst2 + 32, dctTable[3], dctTable[4], dctTable[5], 36);
                    }
                    dst1 += 64;
                    dst2 += 64;
                }
            }
            if (sectorActive) {
                for (int row = 0; row < secH; ++row) {
                    if (dstY + row >= height) break;
                    int copyBytes = Math.Min(secStride, (width - dstX) * 4);
                    Buffer.BlockCopy(secOut, row * secStride, canvas, (dstY + row) * fullStride + dstX * 4, copyBytes);
                }
            }
        }
        for (int k = 3; k < canvas.Length; k += 4) canvas[k] = 0xFF;
    }

    static void Main(string[] args) {
        int step = args.Length > 0 ? int.Parse(args[0]) : 5;
        int tw = args.Length > 1 ? int.Parse(args[1]) : 320;
        int th = args.Length > 2 ? int.Parse(args[2]) : 180;
        long q = args.Length > 3 ? long.Parse(args[3]) : 25L;

        string cmvPath = @"G:\SteamLibrary\steamapps\common\Aoi Tori\data\video\op.cmv";
        string outDir = @"E:\Antigravity\aoitori-rw5\src\common\opening";
        if (Directory.Exists(outDir)) {
            foreach (var old in Directory.GetFiles(outDir, "*.jpg")) File.Delete(old);
        } else {
            Directory.CreateDirectory(outDir);
        }

        var codec = ImageCodecInfo.GetImageEncoders().First(c => c.FormatID == ImageFormat.Jpeg.Guid);
        var ep = new EncoderParameters(1);
        ep.Param[0] = new EncoderParameter(Encoder.Quality, q);

        long totalBytes = 0;
        int outCount = 0;
        int errCount = 0;
        using (var fs = File.OpenRead(cmvPath))
        using (var br = new BinaryReader(fs)) {
            br.ReadBytes(4);
            uint resOff = br.ReadUInt32();
            br.ReadUInt32(); br.ReadUInt32();
            uint maxSeq = br.ReadUInt32();
            uint fps = br.ReadUInt32();
            br.ReadUInt32();
            int width = br.ReadInt32();
            int height = br.ReadInt32();
            byte[] canvas = new byte[width * height * 4];
            for (int k = 3; k < canvas.Length; k += 4) canvas[k] = 0xFF;

            for (uint fid = 0; fid < maxSeq; fid++) {
                fs.Seek(44 + fid * 20, SeekOrigin.Begin);
                uint seq = br.ReadUInt32(), csz = br.ReadUInt32(), usz = br.ReadUInt32(), rtype = br.ReadUInt32(), foff = br.ReadUInt32();
                if (rtype != 2) continue;
                fs.Seek(resOff + foff, SeekOrigin.Begin);
                byte[] jbp = br.ReadBytes((int)csz);
                try {
                    DecodeJbpdIntoBuffer(jbp, canvas, width, height);
                } catch (Exception ex) {
                    errCount++;
                    if (errCount <= 5) Console.WriteLine("Frame {0} ERR: {1}", fid, ex.Message);
                }

                if (fid % (uint)step == 0) {
                    using (var fullBmp = new Bitmap(width, height, PixelFormat.Format32bppArgb)) {
                        var bd = fullBmp.LockBits(new Rectangle(0, 0, width, height), ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
                        Marshal.Copy(canvas, 0, bd.Scan0, canvas.Length);
                        fullBmp.UnlockBits(bd);
                        using (var scaled = new Bitmap(tw, th, PixelFormat.Format24bppRgb))
                        using (var g = Graphics.FromImage(scaled)) {
                            g.InterpolationMode = InterpolationMode.HighQualityBicubic;
                            g.DrawImage(fullBmp, 0, 0, tw, th);
                            string op = Path.Combine(outDir, string.Format("f{0:D4}.jpg", outCount));
                            scaled.Save(op, codec, ep);
                            totalBytes += new FileInfo(op).Length;
                        }
                    }
                    outCount++;
                }
            }
            double effFps = (double)fps / step;
            double durMs = (maxSeq * 1000.0) / fps;
            string meta = string.Format("{{\n  \"frameCount\": {0},\n  \"sourceFrames\": {1},\n  \"sourceFps\": {2},\n  \"step\": {3},\n  \"fps\": {4:F2},\n  \"durationMs\": {5},\n  \"width\": {6},\n  \"height\": {7},\n  \"quality\": {8},\n  \"totalBytes\": {9},\n  \"errCount\": {10}\n}}\n",
                outCount, maxSeq, fps, step, effFps, (int)Math.Round(durMs), tw, th, q, totalBytes, errCount);
            File.WriteAllText(@"E:\Antigravity\aoitori-rw5\src\common\opening-meta.json", meta);
            Console.WriteLine(string.Format("Extracted {0} OP frames ({1:F2} fps, {2:N0} bytes, errs={3})", outCount, effFps, totalBytes, errCount));
        }
    }
}
