import os, zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "IngredientShield-1024-Submission.zip")

# arcname -> local path
mapping = [
    ("index.html", "docs/index.html"),
    ("README.md", "README.md"),
    ("SYNC_ARCHITECTURE.md", "SYNC_ARCHITECTURE.md"),
    ("投稿说明-1024造物挑战.md", "投稿说明-1024造物挑战.md"),
    ("gov_products.json", "docs/gov_products.json"),
    (".github/workflows/sync-gov-data.yml", ".github/workflows/sync-gov-data.yml"),
    ("skills/ingredient-shield/engine/component_db.py", "skills/ingredient-shield/engine/component_db.py"),
    ("skills/ingredient-shield/engine/combination.py", "skills/ingredient-shield/engine/combination.py"),
    ("skills/ingredient-shield/engine/data_source.py", "skills/ingredient-shield/engine/data_source.py"),
    ("skills/ingredient-shield/engine/sync_gov_data.py", "skills/ingredient-shield/engine/sync_gov_data.py"),
    ("skills/ingredient-shield/data/components.json", "skills/ingredient-shield/data/components.json"),
    ("skills/ingredient-shield/data/gov_feed_sample.csv", "skills/ingredient-shield/data/gov_feed_sample.csv"),
]

# screenshots
shot_dir = os.path.join(ROOT, "submit_package", "screenshots")
for fn in sorted(os.listdir(shot_dir)):
    if fn.lower().endswith(".png"):
        mapping.append((os.path.join("screenshots", fn), os.path.join("submit_package", "screenshots", fn)))

if os.path.exists(OUT):
    os.remove(OUT)

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for arc, local in mapping:
        lp = os.path.join(ROOT, local)
        if not os.path.exists(lp):
            print("MISSING:", lp)
            continue
        z.write(lp, arc)
        print("added", arc)

print("\nWROTE", OUT, os.path.getsize(OUT), "bytes")
