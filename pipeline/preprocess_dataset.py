import os
import cv2
from preprocessing import preprocess

INPUT_DIR = "data/samples"
OUTPUT_DIR = "data/processed"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Get all images
files = [f for f in os.listdir(INPUT_DIR)
         if f.lower().endswith((".jpg", ".png", ".jpeg"))]

if not files:
    raise RuntimeError("No images found in data/samples/")

print(f"[INFO] Found {len(files)} images")

for file in files:
    path = os.path.join(INPUT_DIR, file)
    img = cv2.imread(path)

    if img is None:
        print(f"[WARNING] Skipping {file}")
        continue

    gray, smooth, edges = preprocess(img)

    name = os.path.splitext(file)[0]

    # Save outputs
    cv2.imwrite(os.path.join(OUTPUT_DIR, f"{name}_gray.png"), gray)
    cv2.imwrite(os.path.join(OUTPUT_DIR, f"{name}_smooth.png"), smooth)
    cv2.imwrite(os.path.join(OUTPUT_DIR, f"{name}_edges.png"), edges)

    print(f"[OK] Processed {file}")

print("[DONE] Dataset preprocessing complete")
print("Saving to:", os.path.abspath(OUTPUT_DIR))