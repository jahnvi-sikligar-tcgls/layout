# Create and save the floorplan image based on provided JSON
# This is an obsolete code for floorplan image generation

import matplotlib.pyplot as plt

rooms = [
    ("living room_1", 5, 4, 5, 4),
    ("entrance_1", 5, 8, 3, 2),
    ("balcony_1", 8, 8, 3, 2),
    ("kitchen_1", 1, 4, 4, 3),
    ("dining room_1", 1, 7, 4, 2),
    ("storage_1", 1, 2, 3, 2),
    ("bedroom_1", 10, 4, 4, 4),
    ("bathroom_1", 14, 4, 2, 3),
    ("bedroom_2", 10, 0, 4, 4),
    ("bathroom_2", 5, 0, 3, 3),
]

fig, ax = plt.subplots(figsize=(10, 8))

for name, x, y, w, h in rooms:
    rect = plt.Rectangle((x, y), w, h, fill=False)
    ax.add_patch(rect)
    ax.text(x + w/2, y + h/2, name, ha='center', va='center', fontsize=8)

ax.set_xlim(0, 17)
ax.set_ylim(0, 11)
ax.set_aspect('equal')
ax.set_title("Box Floorplan")
plt.grid(True)

# Save the image
file_path = "floorplan.png"
plt.savefig(file_path)
plt.close()

file_path
