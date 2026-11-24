using System;
using System.Collections;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using System.Windows.Media.Imaging;
using GameRes;

class Program
{
    [STAThread]
    static void Main(string[] args)
    {
        string garbroDir = @"E:\Antigravity\tools\downloads\GARbro-Mod";
        AppDomain.CurrentDomain.AssemblyResolve += (s, a) =>
        {
            string name = new AssemblyName(a.Name).Name + ".dll";
            string p = Path.Combine(garbroDir, name);
            return File.Exists(p) ? Assembly.LoadFrom(p) : null;
        };
        try
        {
            AssetDecoder.Run(garbroDir, args);
        }
        catch (Exception ex)
        {
            Console.WriteLine("FATAL: " + ex.GetType().FullName + ": " + ex.Message);
            if (ex.InnerException != null)
            {
                Console.WriteLine("INNER: " + ex.InnerException.GetType().FullName + ": " + ex.InnerException.Message);
                Console.WriteLine(ex.InnerException.StackTrace);
            }
            Console.WriteLine(ex.StackTrace);
            Environment.Exit(1);
        }
    }
}

class MemFileSystem : IFileSystem
{
    private readonly Dictionary<string, byte[]> _files;
    public string CurrentDirectory { get; set; }

    public MemFileSystem(Dictionary<string, byte[]> files)
    {
        _files = files;
        CurrentDirectory = "";
    }

    public Entry FindFile(string filename)
    {
        string key = Path.GetFileName(filename).ToLowerInvariant();
        byte[] data;
        if (!_files.TryGetValue(key, out data))
            throw new FileNotFoundException("Not in MemFS: " + filename);
        return new Entry { Name = key, Type = "image", Size = (uint)data.Length };
    }

    public bool FileExists(string filename)
    {
        return _files.ContainsKey(Path.GetFileName(filename).ToLowerInvariant());
    }

    public Stream OpenStream(Entry entry)
    {
        return new MemoryStream(_files[entry.Name.ToLowerInvariant()], false);
    }

    public IBinaryStream OpenBinaryStream(Entry entry)
    {
        return new BinaryStream(OpenStream(entry), entry.Name);
    }

    public ArcView OpenView(Entry entry)
    {
        throw new NotSupportedException();
    }

    public IEnumerable<Entry> GetFiles()
    {
        foreach (var kv in _files)
            yield return new Entry { Name = kv.Key, Type = "image", Size = (uint)kv.Value.Length };
    }

    public IEnumerable<Entry> GetFiles(string pattern) { return GetFiles(); }
    public IEnumerable<Entry> GetFilesRecursive() { return GetFiles(); }
    public string CombinePath(string p1, string p2) { return Path.GetFileName(p2); }
    public string GetDirectoryName(string path) { return ""; }
    public void Dispose() {}
}

class AssetDecoder
{
    static readonly string RootDir = @"E:\Antigravity\aoitori-rw5";
    static readonly string DataDir = @"G:\SteamLibrary\steamapps\common\Aoi Tori\data";
    static readonly string LonginusImgDir = @"E:\Antigravity\aoitori-rw5\probe\longinus_named\image";

    static ImageCodecInfo GetJpegCodec()
    {
        return ImageCodecInfo.GetImageEncoders().First(c => c.FormatID == System.Drawing.Imaging.ImageFormat.Jpeg.Guid);
    }

    static void SaveJpeg(Bitmap bmp, string outPath, long quality)
    {
        var codec = GetJpegCodec();
        using (var ep = new EncoderParameters(1))
        {
            ep.Param[0] = new EncoderParameter(System.Drawing.Imaging.Encoder.Quality, quality);
            bmp.Save(outPath, codec, ep);
        }
    }

    static Bitmap BitmapSourceToDrawingBitmap(BitmapSource src)
    {
        var converted = new FormatConvertedBitmap(src, System.Windows.Media.PixelFormats.Bgra32, null, 0);
        int w = converted.PixelWidth;
        int h = converted.PixelHeight;
        var bmp = new Bitmap(w, h, PixelFormat.Format32bppArgb);
        var rect = new Rectangle(0, 0, w, h);
        var bd = bmp.LockBits(rect, ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
        try
        {
            converted.CopyPixels(new System.Windows.Int32Rect(0, 0, w, h), bd.Scan0, bd.Stride * h, bd.Stride);
        }
        finally
        {
            bmp.UnlockBits(bd);
        }
        return bmp;
    }

    static Bitmap ResizeBitmapFill16x9(Bitmap src, int targetW, int targetH)
    {
        // Center-crop to target aspect ratio if wider/taller, then HighQualityBicubic scale
        double srcRatio = (double)src.Width / src.Height;
        double dstRatio = (double)targetW / targetH;
        Rectangle crop;
        if (Math.Abs(srcRatio - dstRatio) < 0.02)
        {
            crop = new Rectangle(0, 0, src.Width, src.Height);
        }
        else if (srcRatio > dstRatio)
        {
            int cw = (int)Math.Round(src.Height * dstRatio);
            int cx = Math.Max(0, (src.Width - cw) / 2);
            crop = new Rectangle(cx, 0, Math.Min(cw, src.Width - cx), src.Height);
        }
        else
        {
            int ch = (int)Math.Round(src.Width / dstRatio);
            int cy = Math.Max(0, (src.Height - ch) / 2);
            crop = new Rectangle(0, cy, src.Width, Math.Min(ch, src.Height - cy));
        }

        var dst = new Bitmap(targetW, targetH, PixelFormat.Format24bppRgb);
        using (var g = Graphics.FromImage(dst))
        {
            g.InterpolationMode = InterpolationMode.HighQualityBicubic;
            g.PixelOffsetMode = PixelOffsetMode.HighQuality;
            g.SmoothingMode = SmoothingMode.HighQuality;
            g.DrawImage(src, new Rectangle(0, 0, targetW, targetH), crop, GraphicsUnit.Pixel);
        }
        return dst;
    }

    static Bitmap ResizeBitmapFit(Bitmap src, int maxW, int maxH)
    {
        double scale = Math.Min((double)maxW / src.Width, (double)maxH / src.Height);
        int tw = Math.Max(16, (int)Math.Round(src.Width * scale));
        int th = Math.Max(16, (int)Math.Round(src.Height * scale));
        var dst = new Bitmap(tw, th, PixelFormat.Format24bppRgb);
        using (var g = Graphics.FromImage(dst))
        {
            g.InterpolationMode = InterpolationMode.HighQualityBicubic;
            g.PixelOffsetMode = PixelOffsetMode.HighQuality;
            g.SmoothingMode = SmoothingMode.HighQuality;
            g.DrawImage(src, new Rectangle(0, 0, tw, th), new Rectangle(0, 0, src.Width, src.Height), GraphicsUnit.Pixel);
        }
        return dst;
    }

    static Bitmap ResizeBitmapRgba(Bitmap src, int targetW, int targetH)
    {
        var dst = new Bitmap(targetW, targetH, PixelFormat.Format32bppArgb);
        using (var g = Graphics.FromImage(dst))
        {
            g.InterpolationMode = InterpolationMode.HighQualityBicubic;
            g.PixelOffsetMode = PixelOffsetMode.HighQuality;
            g.SmoothingMode = SmoothingMode.HighQuality;
            g.DrawImage(src, new Rectangle(0, 0, targetW, targetH), new Rectangle(0, 0, src.Width, src.Height), GraphicsUnit.Pixel);
        }
        return dst;
    }

    // Simple JSON string array / sprite map parser for image-requests.json (avoid external deps)
    static void ParseRequests(string jsonText, out List<string> bgs, out Dictionary<string, string> sprites)
    {
        bgs = new List<string>();
        sprites = new Dictionary<string, string>();
        int bStart = jsonText.IndexOf("\"bgs\"");
        int sStart = jsonText.IndexOf("\"sprites\"");
        int bEnd = jsonText.IndexOf("]", bStart);
        foreach (Match m in Regex.Matches(jsonText.Substring(bStart, bEnd - bStart), "\"([^\"]+)\""))
        {
            if (m.Groups[1].Value != "bgs") bgs.Add(m.Groups[1].Value);
        }
        int endS = jsonText.IndexOf("\"bgCount\"");
        string spBlock = jsonText.Substring(sStart, endS - sStart);
        foreach (Match m in Regex.Matches(spBlock, "\"([^\"]+)\":\\s*\\{[^}]*\"base\":\\s*\"([^\"]+)\""))
        {
            sprites[m.Groups[1].Value] = m.Groups[2].Value;
        }
    }

    static Bitmap Quantize256(Bitmap src)
    {
        // Fast 32->8bpp color quantization or keep 32bpp? Wait: let's keep crisp 32bpp RGBA for small face patches & bases first,
        // or test png size! Actually .NET Save(Png) compresses flat cel-shaded anime areas very tightly; we'll measure bytes!
        return src;
    }

    public static void Run(string garbroDir, string[] args)
    {
        bool spritesOnly = args != null && args.Contains("--sprites-only");
        bool cgOnly = args != null && args.Contains("--cg-only");
        bool inspectBgs = args != null && args.Contains("--inspect-bgs");
        bool exportTitleBg = args != null && args.Contains("--export-title-bg");
        bool uiRaw = args != null && args.Contains("--ui-raw");
        long evQuality = 38L;
        long hQuality = 25L;
        long bgQuality = 34L;
        int hWidth = 384;
        int hHeight = 216;
        if (args != null)
        {
            foreach (var a in args)
            {
                if (a.StartsWith("--ev-q=")) long.TryParse(a.Substring(7), out evQuality);
                else if (a.StartsWith("--h-q=")) long.TryParse(a.Substring(6), out hQuality);
                else if (a.StartsWith("--bg-q=")) long.TryParse(a.Substring(7), out bgQuality);
                else if (a.StartsWith("--h-w=")) int.TryParse(a.Substring(6), out hWidth);
                else if (a.StartsWith("--h-h=")) int.TryParse(a.Substring(6), out hHeight);
            }
        }
        Assembly.LoadFrom(Path.Combine(garbroDir, "ArcFormats.dll"));
        using (var fs = File.OpenRead(Path.Combine(garbroDir, "GameData", "Formats.dat")))
        {
            FormatCatalog.Instance.DeserializeScheme(fs);
        }

        var cpzOpener = FormatCatalog.Instance.ArcFormats.First(a => a.GetType().FullName == "GameRes.Formats.Purple.CpzOpener");
        var pb3Format = FormatCatalog.Instance.ImageFormats.First(f => f.GetType().FullName == "GameRes.Formats.Purple.Pb3Format");
        var decryptPb3 = cpzOpener.GetType().GetMethod("DecryptPb3", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static | BindingFlags.Instance);

        Console.WriteLine("Indexing .cpz packs and loose image/*.pb3...");
        var memFiles = new Dictionary<string, byte[]>(StringComparer.OrdinalIgnoreCase);

        // 1. Index loose data/image/**/*.pb3 (decrypting each with DecryptPb3)
        if (!exportTitleBg)
        {
            foreach (string fp in Directory.GetFiles(Path.Combine(DataDir, "image"), "*.pb3", SearchOption.AllDirectories))
            {
                string key = Path.GetFileName(fp).ToLowerInvariant();
                byte[] raw = File.ReadAllBytes(fp);
                decryptPb3.Invoke(cpzOpener, new object[] { raw });
                memFiles[key] = raw;
            }
            Console.WriteLine("  Loose image/*.pb3 indexed: " + memFiles.Count);
        }

        // 2. Index bg.cpz, stand.cpz, up.cpz
        string[] packs = exportTitleBg ? new[] { "bg.cpz" } : new[] { "bg.cpz", "stand.cpz", "up.cpz" };
        foreach (string arcName in packs)
        {
            string arcPath = Path.Combine(DataDir, "pack", arcName);
            using (var view = new ArcView(arcPath))
            using (var arc = cpzOpener.TryOpen(view))
            {
                int cnt = 0;
                foreach (var entry in arc.Dir)
                {
                    if (!entry.Name.EndsWith(".pb3", StringComparison.OrdinalIgnoreCase)) continue;
                    string key = Path.GetFileName(entry.Name).ToLowerInvariant();
                    using (var s = arc.OpenEntry(entry))
                    using (var ms = new MemoryStream())
                    {
                        s.CopyTo(ms);
                        memFiles[key] = ms.ToArray();
                        cnt++;
                    }
                }
                Console.WriteLine("  Pack {0}: {1} .pb3 entries loaded", arcName, cnt);
            }
        }

        // Push MemFS onto VFS.m_vfs so Pb3Format.Read resolves all diff base images automatically!
        var mVfsField = typeof(VFS).GetField("m_vfs", BindingFlags.NonPublic | BindingFlags.Static);
        var vfsStack = mVfsField.GetValue(null);
        var pushMethod = vfsStack.GetType().GetMethod("Push", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
        var memFs = new MemFileSystem(memFiles);
        pushMethod.Invoke(vfsStack, new object[] { "mem", memFs });

        Func<string, Bitmap> decodePb3 = (basename) =>
        {
            string key = (basename.EndsWith(".pb3") ? basename : basename + ".pb3").ToLowerInvariant();
            byte[] raw;
            if (!memFiles.TryGetValue(key, out raw)) return null;
            using (var ms = new MemoryStream(raw, false))
            using (var bs = new BinaryStream(ms, key))
            {
                var meta = pb3Format.ReadMetaData(bs);
                bs.Position = 0;
                var imgData = pb3Format.Read(bs, meta);
                return BitmapSourceToDrawingBitmap(imgData.Bitmap);
            }
        };

        // Also check Longinus localized 32-bit BGRA images (e.g. eyecatch00..06, ev_etc06a..e, ev_etc24a, title01..03_chip, unlock01..05)
        Func<string, int, Bitmap> loadLonginusOverride = (basename, fallbackWidth) =>
        {
            string lp = Path.Combine(LonginusImgDir, basename + ".pb3");
            if (!File.Exists(lp)) return null;
            byte[] raw = File.ReadAllBytes(lp);
            int w = fallbackWidth;
            // Detect width from original pb3 metadata if present
            string key = (basename + ".pb3").ToLowerInvariant();
            if (memFiles.ContainsKey(key))
            {
                using (var ms = new MemoryStream(memFiles[key], false))
                using (var bs = new BinaryStream(ms, key))
                {
                    var meta = pb3Format.ReadMetaData(bs);
                    if (meta != null) w = (int)meta.Width;
                }
            }
            if (raw.Length % (w * 4) != 0) return null;
            int h = raw.Length / (w * 4);
            var bmp = new Bitmap(w, h, PixelFormat.Format32bppArgb);
            var bd = bmp.LockBits(new Rectangle(0, 0, w, h), ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
            System.Runtime.InteropServices.Marshal.Copy(raw, 0, bd.Scan0, raw.Length);
            bmp.UnlockBits(bd);
            return bmp;
        };

        // Load image-requests.json
        List<string> bgs;
        Dictionary<string, string> sprites;
        ParseRequests(File.ReadAllText(Path.Combine(RootDir, "converted", "image-requests.json"), Encoding.UTF8), out bgs, out sprites);
        Console.WriteLine("Requests: BGs=" + bgs.Count + ", Sprites=" + sprites.Count);

        string outImgDir = Path.Combine(RootDir, "src", "common", "images");
        string outSpDir = Path.Combine(RootDir, "src", "common", "sprites");
        string outFaceDir = Path.Combine(RootDir, "src", "common", "faces");
        Directory.CreateDirectory(outImgDir);
        Directory.CreateDirectory(outSpDir);
        Directory.CreateDirectory(outFaceDir);

        if (uiRaw)
        {
            string uiRawDir = Path.Combine(RootDir, "probe", "ui_raw");
            Directory.CreateDirectory(uiRawDir);
            foreach (string uiName in new[] { "message01", "message02", "logo", "dialog_chip", "iconwindow" })
            {
                Bitmap u = loadLonginusOverride(uiName, 1280);
                if (u == null) u = decodePb3(uiName);
                if (u != null)
                {
                    using (u)
                    {
                        u.Save(Path.Combine(uiRawDir, uiName + ".png"), System.Drawing.Imaging.ImageFormat.Png);
                        Console.WriteLine("Decoded UI raw: " + uiName + " " + u.Width + "x" + u.Height);
                    }
                }
            }
        }

        if (exportTitleBg)
        {
            string titleSrcDir = Path.Combine(RootDir, "probe", "title_src");
            Directory.CreateDirectory(titleSrcDir);
            foreach (string stem in new[] { "bg520a", "bg520c" })
            {
                using (var bmp = decodePb3(stem))
                {
                    if (bmp != null)
                    {
                        string outP = Path.Combine(titleSrcDir, stem + ".png");
                        bmp.Save(outP, System.Drawing.Imaging.ImageFormat.Png);
                        Console.WriteLine("Exported title BG: " + stem + " " + bmp.Width + "x" + bmp.Height);
                    }
                }
            }
            return;
        }

        if (inspectBgs)
        {
            var shapeCounts = new Dictionary<string, int>();
            var non16x9 = new List<string>();
            foreach (string stem in bgs)
            {
                if (stem == "black" || stem == "white" || stem == "red" || stem == "blue") continue;
                Bitmap rawBmp = loadLonginusOverride(stem, 1280);
                if (rawBmp == null) rawBmp = decodePb3(stem);
                if (rawBmp == null) continue;
                using (rawBmp)
                {
                    string dim = rawBmp.Width + "x" + rawBmp.Height;
                    int c; shapeCounts.TryGetValue(dim, out c); shapeCounts[dim] = c + 1;
                    double r = (double)rawBmp.Width / rawBmp.Height;
                    if (Math.Abs(r - 16.0 / 9.0) >= 0.03)
                    {
                        non16x9.Add(stem + ":" + dim);
                    }
                }
            }
            foreach (var kv in shapeCounts.OrderByDescending(x => x.Value))
                Console.WriteLine("SHAPE " + kv.Key + " => " + kv.Value);
            Console.WriteLine("NON_16X9_COUNT=" + non16x9.Count);
            foreach (var s in non16x9.Take(80)) Console.WriteLine("  " + s);
            return;
        }

        // Decode BGs / CGs (skip when --sprites-only is passed and files already exist)
        int bgOk = 0, bgMissing = 0;
        long bgBytes = 0;
        var missingList = new List<string>();
        if (!spritesOnly)
        {
            foreach (string stem in bgs)
            {
                if (stem == "black" || stem == "white" || stem == "red" || stem == "blue")
                {
                    using (var sb = new Bitmap(16, 9, PixelFormat.Format24bppRgb))
                    using (var g = Graphics.FromImage(sb))
                    {
                        g.Clear(stem == "white" ? Color.White : (stem == "red" ? Color.DarkRed : (stem == "blue" ? Color.Navy : Color.Black)));
                        string op = Path.Combine(outImgDir, stem + ".jpg");
                        SaveJpeg(sb, op, 30);
                        bgBytes += new FileInfo(op).Length;
                    }
                    bgOk++;
                    continue;
                }
                Bitmap rawBmp = loadLonginusOverride(stem, 1280);
                if (rawBmp == null) rawBmp = decodePb3(stem);
                if (rawBmp == null)
                {
                    bgMissing++;
                    missingList.Add(stem);
                    continue;
                }
                using (rawBmp)
                {
                    bool isAdult = stem.StartsWith("h_");
                    bool isEvent = stem.StartsWith("ev");
                    long q = isAdult ? hQuality : (isEvent ? evQuality : bgQuality);
                    double ratio = (double)rawBmp.Width / rawBmp.Height;
                    Bitmap resized;
                    if (ratio < 1.72)
                    {
                        // Preserve 100% of tall/square CGs/BGs without cropping heads or boots
                        resized = ResizeBitmapFit(rawBmp, 400, 360);
                    }
                    else
                    {
                        int tw = isAdult ? hWidth : 432;
                        int th = isAdult ? hHeight : 243;
                        resized = ResizeBitmapFill16x9(rawBmp, tw, th);
                    }
                    using (resized)
                    {
                        string op = Path.Combine(outImgDir, stem + ".jpg");
                        SaveJpeg(resized, op, q);
                        bgBytes += new FileInfo(op).Length;
                    }
                    bgOk++;
                }
            }
            if (!cgOnly)
            {
                for (int i = 1; i <= 3; i++)
                {
                    string tName = string.Format("title0{0}_chip", i);
                    using (var full = loadLonginusOverride(tName, 1280))
                    {
                        if (full != null)
                        {
                            using (var crop = full.Clone(new Rectangle(0, 0, 1280, 720), PixelFormat.Format32bppArgb))
                            using (var res = ResizeBitmapFill16x9(crop, 432, 243))
                            {
                                string op = Path.Combine(outImgDir, string.Format("title0{0}.jpg", i));
                                SaveJpeg(res, op, 42L);
                                bgBytes += new FileInfo(op).Length;
                            }
                        }
                    }
                }
            }
            for (int i = 1; i <= 5; i++)
            {
                string uName = string.Format("unlock0{0}", i);
                using (var u = loadLonginusOverride(uName, 1280))
                {
                    if (u != null)
                    {
                        using (var res = ResizeBitmapFill16x9(u, 432, 243))
                        {
                            string op = Path.Combine(outImgDir, uName + ".jpg");
                            SaveJpeg(res, op, evQuality);
                            bgBytes += new FileInfo(op).Length;
                        }
                    }
                }
            }
            Console.WriteLine(string.Format("BGs decoded: ok={0}, missing={1}, totalBytes={2:N0} (evQ={3}, hQ={4}, bgQ={5})", bgOk, bgMissing, bgBytes, evQuality, hQuality, bgQuality));
            if (missingList.Count > 0) Console.WriteLine("  Missing BGs sample: " + string.Join(", ", missingList.Take(10)));
        }

        if (cgOnly)
        {
            return;
        }

        // Re-decode all sprites with true native aspect ratio and record probe/sprite_dims.json
        string rawSpOutDir = Path.Combine(RootDir, "probe", "sprites_scaled");
        Directory.CreateDirectory(rawSpOutDir);
        foreach (string oldPng in Directory.GetFiles(rawSpOutDir, "*.png"))
        {
            File.Delete(oldPng);
        }
        int spOk = 0, spMissing = 0;
        var dimsLines = new List<string>();
        foreach (var kv in sprites.OrderBy(k => k.Key, StringComparer.Ordinal))
        {
            string asset = kv.Key;
            string outP = Path.Combine(rawSpOutDir, asset + ".png");
            using (var raw = decodePb3(asset))
            {
                if (raw == null) { spMissing++; continue; }
                int tw, th, cropH;
                if (raw.Width == 512 && raw.Height == 512)
                {
                    tw = 144;
                    th = 144;
                    cropH = 144;
                }
                else if (asset.StartsWith("up-"))
                {
                    double scale = 256.0 / raw.Height;
                    tw = Math.Max(16, (int)Math.Round(raw.Width * scale));
                    th = 256;
                    cropH = 256;
                }
                else
                {
                    double scale = 360.0 / raw.Height;
                    tw = Math.Max(16, (int)Math.Round(raw.Width * scale));
                    th = 360;
                    cropH = Math.Min(296, th);
                }
                using (var scaled = ResizeBitmapRgba(raw, tw, th))
                {
                    if (cropH < scaled.Height)
                    {
                        using (var cropped = scaled.Clone(new Rectangle(0, 0, tw, cropH), PixelFormat.Format32bppArgb))
                        {
                            cropped.Save(outP, System.Drawing.Imaging.ImageFormat.Png);
                        }
                    }
                    else
                    {
                        scaled.Save(outP, System.Drawing.Imaging.ImageFormat.Png);
                    }
                }
                dimsLines.Add(string.Format("  \"{0}\": [{1}, {2}, {3}, {4}]", asset, tw, cropH, raw.Width, raw.Height));
                spOk++;
            }
        }
        string dimsJson = "{\n" + string.Join(",\n", dimsLines) + "\n}\n";
        File.WriteAllText(Path.Combine(RootDir, "probe", "sprite_dims.json"), dimsJson, Encoding.UTF8);
        Console.WriteLine(string.Format("Sprites scaled to probe/sprites_scaled/: ok={0}, missing={1}", spOk, spMissing));
    }
}
