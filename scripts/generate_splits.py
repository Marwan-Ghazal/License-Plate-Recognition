 
from __future__ import annotations
 
import random
from pathlib import Path
 
 
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLES_DIR  = PROJECT_ROOT / "data" / "samples"
SPLITS_DIR   = PROJECT_ROOT / "data" / "splits"
 
GOLDEN_INDICES = [0, 1, 8, 9, 32]
EVAL_SIZE      = 50
SEED           = 42
 
TOTAL_IMAGES   = 433  # Cars0.png to Cars432.png
 
 
def main() -> None:
    SPLITS_DIR.mkdir(parents=True, exist_ok=True)
 
    # Generate the canonical filename list (we don't depend on data/samples/
    # actually existing — the splits are valid even before anyone downloads).
    all_names = [f"Cars{i}.png" for i in range(TOTAL_IMAGES)]
 
    # Sanity check against disk if the dataset is present
    if SAMPLES_DIR.exists():
        on_disk = {p.name for p in SAMPLES_DIR.iterdir() if p.is_file()}
        missing = [n for n in all_names if n not in on_disk]
        if missing:
            print(f"[WARN] {len(missing)} expected images not found on disk; "
                  f"first few: {missing[:5]}")
    else:
        print(f"[INFO] {SAMPLES_DIR} not found — generating splits from "
              f"the canonical filename list anyway.")
 
    # Golden: fixed indices
    golden = [f"Cars{i}.png" for i in GOLDEN_INDICES]
 
    # Pool for random sampling = everything not in golden
    golden_set = set(golden)
    pool       = [n for n in all_names if n not in golden_set]
 
    rng = random.Random(SEED)
    rng.shuffle(pool)
 
    eval_ = sorted(pool[:EVAL_SIZE])
    dev   = sorted(pool[EVAL_SIZE:])
 
    # Sanity: no overlap, full coverage
    assert len(set(golden) & set(eval_)) == 0
    assert len(set(golden) & set(dev))   == 0
    assert len(set(eval_)  & set(dev))   == 0
    assert len(golden) + len(eval_) + len(dev) == TOTAL_IMAGES
 
    # Write out
    write_split("golden.txt", golden)
    write_split("eval.txt",   eval_)
    write_split("dev.txt",    dev)
 
    print(f"[OK] Wrote splits to {SPLITS_DIR}")
    print(f"     golden : {len(golden):>3} images  ({', '.join(golden)})")
    print(f"     eval   : {len(eval_):>3} images")
    print(f"     dev    : {len(dev):>3} images")
 
 
def write_split(name: str, items: list[str]) -> None:
    path = SPLITS_DIR / name
    path.write_text("\n".join(items) + "\n", encoding="utf-8")
 
 
if __name__ == "__main__":
    main()