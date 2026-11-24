using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;

class JbpdDecoder {
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

    static void DecodeJbpd(string inPath, string outPng) {
        byte[] input = File.ReadAllBytes(inPath);
        int dataPos = BitConverter.ToInt32(input, 4); // 44
        int width = BitConverter.ToUInt16(input, 0x10);
        int height = BitConverter.ToUInt16(input, 0x12);
        int dcLen = BitConverter.ToInt32(input, 0x1C);
        int acLen = BitConverter.ToInt32(input, 0x20);
        uint sectorMask = BitConverter.ToUInt32(input, dataPos); // 0x2c

        var freq = new uint[0x20];
        Buffer.BlockCopy(input, dataPos + 4, freq, 0, 0x40);
        var treeData = new byte[0x10];
        int treePos = dataPos + 4 + 0x80; // 0xb0
        for (int i = 0; i < 0x10; ++i) treeData[i] = (byte)(input[treePos + i] + 1);
        var treeDc = new HuffmanTree(treeData, freq);
        Buffer.BlockCopy(input, dataPos + 4 + 0x40, freq, 0, 0x40);
        var treeAc = new HuffmanTree(treeData, freq);

        int quantPos = treePos + 0x10; // 0xc0
        var quantY = new short[0x40];
        var quantC = new short[0x40];
        for (int i = 0; i < 0x40; ++i) {
            quantY[i] = input[quantPos + i];
            quantC[i] = input[quantPos + 0x40 + i];
        }

        int gridPos = quantPos + 0x80; // 0x140
        int rows = input[gridPos];
        int cols = input[gridPos + 1];
        int nSectors = input[gridPos + 2];
        int bitsOffset = (gridPos + 4 + nSectors * 2 + 3) & ~3;

        var bitsDc = new JBitStream(input, bitsOffset, dcLen);
        var bitsAc = new JBitStream(input, bitsOffset + dcLen, acLen);

        int totalActiveBlocks = 0;
        for (int s = 0; s < nSectors; ++s) {
            if ((sectorMask & (1u << s)) != 0) {
                int bh = input[gridPos + 4 + s * 2];
                int bw = input[gridPos + 4 + s * 2 + 1];
                totalActiveBlocks += bh * bw;
            }
        }

        var blocks = new short[totalActiveBlocks, 6];
        uint prevV = 0;
        for (int i = 0; i < totalActiveBlocks; ++i)
        for (int j = 0; j < 6; ++j) {
            int bc = treeDc.Read(bitsDc);
            uint v = (uint)bitsDc.GetBits(bc);
            if (v < (1u << (bc - 1))) v -= (1u << bc) - 1;
            prevV += v;
            blocks[i, j] = (short)prevV;
        }

        int fullStride = width * 4;
        byte[] output = new byte[fullStride * height];
        for (int k = 3; k < output.Length; k += 4) output[k] = 0xFF;

        var dctTable = new short[6][];
        for (int i = 0; i < 6; ++i) dctTable[i] = new short[64];

        int blkIdx = 0;
        for (int s = 0; s < nSectors; ++s) {
            if ((sectorMask & (1u << s)) == 0) continue;
            int sr = s / cols;
            int sc = s % cols;
            int bh = input[gridPos + 4 + s * 2];
            int bw = input[gridPos + 4 + s * 2 + 1];
            int secW = bw * 16;
            int secH = bh * 16;
            int secStride = secW * 4;
            byte[] secOut = new byte[secStride * secH];
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
                    dst1 += 64;
                    dst2 += 64;
                }
            }
            int dstX = sc * 256;
            int dstY = sr * 256;
            for (int row = 0; row < secH; ++row) {
                if (dstY + row >= height) break;
                int copyBytes = Math.Min(secStride, (width - dstX) * 4);
                Buffer.BlockCopy(secOut, row * secStride, output, (dstY + row) * fullStride + dstX * 4, copyBytes);
            }
        }
        // Force alpha 255
        for (int k = 3; k < output.Length; k += 4) output[k] = 0xFF;

        using (var bmp = new Bitmap(width, height, PixelFormat.Format32bppArgb)) {
            var bd = bmp.LockBits(new Rectangle(0, 0, width, height), ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
            Marshal.Copy(output, 0, bd.Scan0, output.Length);
            bmp.UnlockBits(bd);
            bmp.Save(outPng, ImageFormat.Png);
        }
        Console.WriteLine("Saved " + outPng + " (" + width + "x" + height + ", blocks=" + blkIdx + ")");
    }

    static void Main() {
        DecodeJbpd(@"E:\Antigravity\aoitori-rw5\probe\op_frame100.jbp", @"E:\Antigravity\aoitori-rw5\probe\op_frame100_jbpd.png");
        DecodeJbpd(@"E:\Antigravity\aoitori-rw5\probe\bg070a_frame0.jbp", @"E:\Antigravity\aoitori-rw5\probe\bg070a_frame0_jbpd.png");
    }
}
