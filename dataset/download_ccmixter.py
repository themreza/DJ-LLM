"""
A script to download the selected music from ccMixter.
For each ccMixter upload, it only downloads the first file that is in MP3 format.
It saves the files in a directory called music, wherever the script itself is located,
saving the file as <upload_id>_<file_index>.mp3.
Before running this script, make sure to run fetch_ccmixter.py to get the data from
ccMixter, and then run select_ccmixter.py to create selected_uploads.txt, containing
selected upload IDs.
"""

import json
import sys
import ssl
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError


def read_selected_uploads(filepath):
    upload_ids = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                upload_ids.append(int(line))
    return upload_ids


def find_upload_data(upload_id, jsonl_filepath):
    with open(jsonl_filepath, 'r') as f:
        for line in f:
            data = json.loads(line)
            if data.get('upload_id') == upload_id:
                return data
    return None


def get_first_mp3_file(upload_data):
    files = upload_data.get('files', [])
    for idx, file_info in enumerate(files):
        format_info = file_info.get('file_format_info', {})
        if format_info.get('default-ext') == 'mp3' or file_info.get('file_name', '').endswith('.mp3'):
            return idx, file_info
    return None, None


def download_file(url, output_path):
    try:
        print(f"  Downloading from: {url}")

        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        req = Request(url)
        req.add_header('Referer', 'https://ccmixter.org/')
        req.add_header('User-Agent', 'DJ-LLM')

        with urlopen(req, context=ssl_context) as response:
            with open(output_path, 'wb') as out_file:
                out_file.write(response.read())

        print(f"  Saved to: {output_path}")
        return True
    except URLError as e:
        print(f"  Error downloading file: {e}")
        return False
    except Exception as e:
        print(f"  Unexpected error: {e}")
        return False


def main():
    script_dir = Path(__file__).parent

    selected_uploads_file = script_dir / 'selected_uploads.txt'
    ccmixter_data_file = script_dir / 'ccmixter_data.jsonl'
    music_dir = script_dir / 'music'

    if not selected_uploads_file.exists():
        print(f"Error: {selected_uploads_file} not found!")
        sys.exit(1)

    if not ccmixter_data_file.exists():
        print(f"Error: {ccmixter_data_file} not found!")
        sys.exit(1)

    music_dir.mkdir(exist_ok=True)
    print(f"Music directory: {music_dir}")

    print(f"\nReading upload IDs from {selected_uploads_file}...")
    upload_ids = read_selected_uploads(selected_uploads_file)
    print(f"Found {len(upload_ids)} upload IDs to process")

    success_count = 0
    skip_count = 0
    error_count = 0

    for i, upload_id in enumerate(upload_ids, 1):
        print(f"\n[{i}/{len(upload_ids)}] Processing upload ID: {upload_id}")

        upload_data = find_upload_data(upload_id, ccmixter_data_file)
        if not upload_data:
            print(f"  Warning: Upload ID {upload_id} not found in ccmixter_data.jsonl")
            error_count += 1
            continue

        file_idx, file_info = get_first_mp3_file(upload_data)
        if file_info is None:
            print(f"  Warning: No MP3 file found for upload ID {upload_id}")
            error_count += 1
            continue

        download_url = file_info.get('download_url')
        if not download_url:
            print(f"  Warning: No download URL found for upload ID {upload_id}")
            error_count += 1
            continue

        output_filename = f"{upload_id}_{file_idx}.mp3"
        output_path = music_dir / output_filename

        if output_path.exists():
            file_size = output_path.stat().st_size
            print(f"  File already exists ({file_size} bytes), skipping...")
            skip_count += 1
            continue

        if download_file(download_url, output_path):
            success_count += 1
        else:
            error_count += 1

    print("\n" + "=" * 60)
    print("Download Summary:")
    print(f"  Total uploads processed: {len(upload_ids)}")
    print(f"  Successfully downloaded: {success_count}")
    print(f"  Skipped (already exists): {skip_count}")
    print(f"  Errors: {error_count}")
    print("=" * 60)


if __name__ == '__main__':
    main()
