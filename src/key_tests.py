import json, pathlib, collections

names = collections.defaultdict(set)
miss = collections.defaultdict(set)
bodies = collections.defaultdict(set)
dup_within_file = 0
dup2_within_file = 0

for f in sorted(pathlib.Path("data/raw").rglob("*.json")):
    data = json.loads(f.read_text(encoding="utf-8"))
    neo = data.get("near_earth_objects", [data])  # lookup: tek asteroid nesnesi
    if isinstance(neo, dict):
        neo = [a for day in neo.values() for a in day]
    seen = collections.Counter()
    seen2 = collections.Counter()
    for a in neo:
        names[a["id"]].add(a["name"])
        for c in a.get("close_approach_data", []):
            k2 = (a["id"], c["epoch_date_close_approach"])
            k = (*k2, c["orbiting_body"])
            seen2[k2] += 1
            seen[k] += 1
            miss[k].add(c["miss_distance"]["kilometers"])
            bodies[k2].add(c["orbiting_body"])
    dup_within_file += sum(v > 1 for v in seen.values())
    dup2_within_file += sum(v > 1 for v in seen2.values())

print("0. Tekrar eden (id, epoch) - gövde olmadan, aynı dosya içinde:", dup2_within_file)
print("1. Tekrar eden (id, epoch, gövde), aynı dosya içinde:", dup_within_file)
print("2. Adı dosyalar arasında değişen asteroid:", sum(len(v) > 1 for v in names.values()))
print("3. Aynı anahtar, farklı mesafe değeri:", sum(len(v) > 1 for v in miss.values()))
print("4. Aynı (id, epoch), birden fazla gövde:", sum(len(v) > 1 for v in bodies.values()))