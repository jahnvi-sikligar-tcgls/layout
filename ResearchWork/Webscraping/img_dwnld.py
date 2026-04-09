import pandas as pd
import requests
import os
from urllib.parse import urlparse

# Load the dataset containing image URLs
#df_images = pd.read_csv('property_images_list.csv')
df_images = pd.read_csv('clstr_pln_images_list.csv', dtype=str) # Ensure all data is read as strings to avoid issues with NaN values
# Create a directory to store the images if it doesn't exist
image_dir = 'images_090426'

if not os.path.exists(image_dir):
    os.makedirs(image_dir)

# Function to download an image
def download_image(url, folder, filename=None):
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)

        if not filename:
            # Extract filename from URL, or create a generic one
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            if not filename:
                filename = f"image_{hash(url)}.jpg" # Fallback if no filename in URL path

        file_path = os.path.join(folder, filename)
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return False

# Iterate through each image in the DataFrame and download it
print(f"Starting image download. Total images to process: {len(df_images)}")

downloaded_count = 0
for index, row in df_images.iterrows():
    image_url = row['image_url']
    property_title = str(row['property_title']).replace('/', '_').replace('\\', '_') # Sanitize title for filename
    # Ensure image_caption is a string before calling replace
    image_caption = str(row['image_caption']).replace('/', '_').replace('\\', '_') # Sanitize caption

    # Try to create a unique filename using title, caption, and index
    # Limit filename length to avoid OS issues
    base_filename = f"{property_title}_{image_caption}_{index}"
    base_filename = base_filename[:100] # Truncate to a reasonable length

    # Determine file extension from URL, default to .jpg if not clear
    ext = os.path.splitext(urlparse(image_url).path)[1]
    if not ext or len(ext) > 5: # Basic check for valid extension
        ext = '.jpg'
    elif 'youtube' in image_url: # Handle youtube video thumbnails
        ext = '.jpg'

    full_filename = f"{base_filename}{ext}"

    if download_image(image_url, image_dir, full_filename):
        downloaded_count += 1
        if downloaded_count % 10 == 0:
            print(f"Downloaded {downloaded_count} images...")

print(f"\nFinished downloading. Successfully downloaded {downloaded_count} images to the '{image_dir}' folder.")