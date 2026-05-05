import cv2
import os
import matplotlib.pyplot as plt

OUTPUT_DIR = "data/outputs"


def load_image(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Image not found: {path}")

    img = cv2.imread(path)

    if img is None:
        raise ValueError(f"Failed to read image: {path}")

    return img


def save_debug(image, name):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    path = os.path.join(OUTPUT_DIR, f"{name}.png")

    if image.dtype != "uint8":
        image = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX)
        image = image.astype("uint8")

    cv2.imwrite(path, image)


def show_grid(images, titles):
    n = len(images)
    plt.figure(figsize=(4 * n, 4))

    for i in range(n):
        plt.subplot(1, n, i + 1)

        if len(images[i].shape) == 2:
            plt.imshow(images[i], cmap="gray")
        else:
            plt.imshow(cv2.cvtColor(images[i], cv2.COLOR_BGR2RGB))

        plt.title(titles[i])
        plt.axis("off")

    plt.tight_layout()
    plt.show()