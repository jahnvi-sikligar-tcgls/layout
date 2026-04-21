""" floorplan segmentation """

import cv2
import numpy as np
import os

def segment_units(image_path, output_dir="output_units"):
    os.makedirs(output_dir, exist_ok=True)

    # Load image
    img = cv2.imread(image_path)
    original = img.copy()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Step 1: Threshold → detect walls (dark lines)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    # Step 2: Strengthen walls (VERY IMPORTANT)
    kernel = np.ones((5,5), np.uint8)
    walls = cv2.dilate(thresh, kernel, iterations=2)

    # Step 3: Invert → get free space (rooms)
    free_space = cv2.bitwise_not(walls)

    # Step 4: Connected components
    num_labels, labels = cv2.connectedComponents(free_space)

    h, w = gray.shape

    print(f"Total regions detected: {num_labels}")

    unit_count = 0

    # Debug image (colored regions)
    debug = np.zeros_like(img)

    for label in range(1, num_labels):  # skip background
        mask = (labels == label).astype("uint8") * 255

        area = cv2.countNonZero(mask)

        # Filter (tune these numbers if needed)
        if area < 8000:   # too small → ignore
            continue
        if area > (h * w) * 0.6:  # too big → ignore (floor/lobby)
            continue

        # Extract region
        result = cv2.bitwise_and(original, original, mask=mask)

        # Bounding box
        ys, xs = np.where(mask == 255)
        x1, x2 = xs.min(), xs.max()
        y1, y2 = ys.min(), ys.max()

        crop = result[y1:y2, x1:x2]

        # Save crop
        path = os.path.join(output_dir, f"unit_{unit_count}.png")
        cv2.imwrite(path, crop)

        print(f"Saved: {path} | Area: {area}")

        # Add color to debug image
        color = np.random.randint(0,255, size=3)
        debug[mask == 255] = color

        unit_count += 1

    # Save debug visualization
    cv2.imwrite(os.path.join(output_dir, "debug_segments.png"), debug)

    print(f"\n Final Units Detected: {unit_count}")
    print(f" Debug image saved at: {output_dir}/debug_segments.png")


# -----------------------------
# RUN THIS
# -----------------------------
if __name__ == "__main__":
    image_path = "/content/page23_img76.png"  # <-- change to your file

    segment_units(image_path)

!zip -r /content/output_units.zip /content/output_units
