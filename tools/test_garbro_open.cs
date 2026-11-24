using System;
using System.Collections;
using System.IO;
using System.Linq;
using System.Reflection;

class TestGarbroOpen {
    static void Main() {
        var dir = @"E:\Antigravity\tools\downloads\GARbro-Mod";
        AppDomain.CurrentDomain.AssemblyResolve += (s, a) => {
            var name = new AssemblyName(a.Name).Name + ".dll";
            var p = Path.Combine(dir, name);
            return File.Exists(p) ? Assembly.LoadFrom(p) : null;
        };
        try {
            var gameRes = Assembly.LoadFrom(Path.Combine(dir, "GameRes.dll"));
            var arcFormats = Assembly.LoadFrom(Path.Combine(dir, "ArcFormats.dll"));

            var catalogType = gameRes.GetType("GameRes.FormatCatalog");
            var catalog = catalogType.GetProperty("Instance").GetValue(null);
            // Call LookupFileName / DeserializeScheme
            var schemesPath = Path.Combine(dir, "GameData", "Formats.dat");
            using (var fs = File.OpenRead(schemesPath)) {
                catalogType.GetMethod("DeserializeScheme").Invoke(catalog, new object[] { fs });
            }

            var cpzOpenerType = arcFormats.GetType("GameRes.Formats.Purple.CpzOpener");
            // Check how FormatCatalog stores schemes (Formats property)
            var formatsProp = catalogType.GetProperty("ArcFormats");
            if (formatsProp != null) {
                var arcs = (IEnumerable)formatsProp.GetValue(catalog);
                foreach (var a in arcs) {
                    if (a.GetType() == cpzOpenerType) {
                        var schemeProp = a.GetType().GetProperty("Scheme");
                        var scheme = schemeProp.GetValue(a);
                        Console.WriteLine("Found CpzOpener in FormatCatalog! Scheme = " + (scheme == null ? "NULL" : scheme.GetType().FullName));
                        if (scheme != null) {
                            var ks = (IDictionary)scheme.GetType().GetField("KnownSchemes").GetValue(scheme);
                            Console.WriteLine("KnownSchemes count: " + ks.Count);
                            foreach (DictionaryEntry de in ks) {
                                Console.WriteLine("  " + de.Key);
                            }
                        }
                        // Try opening ps.cpz!
                        var arcViewType = gameRes.GetType("GameRes.ArcView");
                        var psPath = @"G:\SteamLibrary\steamapps\common\Aoi Tori\data\pack\ps.cpz";
                        using (var view = (IDisposable)Activator.CreateInstance(arcViewType, new object[] { psPath })) {
                            var arc = a.GetType().GetMethod("TryOpen").Invoke(a, new object[] { view });
                            Console.WriteLine("ps.cpz TryOpen: " + (arc == null ? "NULL" : arc.GetType().FullName));
                            if (arc != null) {
                                var dirProp = arc.GetType().GetProperty("Dir");
                                var entries = (IEnumerable)dirProp.GetValue(arc);
                                foreach (var entry in entries) {
                                    var name = entry.GetType().GetProperty("Name").GetValue(entry);
                                    var size = entry.GetType().GetProperty("Size").GetValue(entry);
                                    Console.WriteLine("  ps.cpz entry: " + name + " (" + size + " B)");
                                }
                            }
                        }
                    }
                }
            }
        } catch (Exception ex) {
            Console.WriteLine("ERR: " + ex);
        }
    }
}
