import json, pathlib, collections

names = collections.defaultdict(set)
miss = collections.defaultdict(set)
bodies = collections.defaultdict(set)
dup_within_file = 0

for f in sorted(pathlib.Path("data/raw").rglob("*.json")):
    data = json.loads(f.read_text(encoding="utf-8"))
    neo = data["near_earth_objects"]
    if isinstance(neo, dict):
        neo = [a for day in neo.values() for a in day]
    seen = collections.Counter()
    for a in neo:
        names[a["id"]].add(a["name"])
        for c in a.get("close_approach_data", []):
            k = (a["id"], c["epoch_date_close_approach"])
            seen[k] += 1
            miss[k].add(c["miss_distance"]["kilometers"])
            bodies[k].add(c["orbiting_body"])
    dup_within_file += sum(v > 1 for v in seen.values())

print("1. Tekrar eden (id, epoch), aynı dosya içinde:", dup_within_file)
print("2. Adı dosyalar arasında değişen asteroid:", sum(len(v) > 1 for v in names.values()))
print("3. Aynı anahtar, farklı mesafe değeri:", sum(len(v) > 1 for v in miss.values()))
print("4. Aynı anahtar, birden fazla gövde:", sum(len(v) > 1 for v in bodies.values()))