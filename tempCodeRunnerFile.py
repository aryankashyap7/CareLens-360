from google.cloud import storage
import os

def download_all_blobs(bucket_name, destination_folder):
    """Downloads all blobs from the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs()
    os.makedirs(destination_folder, exist_ok=True)
    for blob in blobs:
        dest_path = os.path.join(destination_folder, blob.name)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        blob.download_to_filename(dest_path)
        print(f"Downloaded {blob.name} to {dest_path}.")

# Example usage:
download_all_blobs('client-data-conf', './downloaded_files')