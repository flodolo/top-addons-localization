#! /usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import os
import requests
import shutil
import sys
import zipfile


# This script uses the metadata to download each XPI, and analyze the available
# localizations within each package.
#
# A "support_files" folder is used to store the files, while the resulting data
# is stored in data/analysis.csv


def download_xpi(addon_data, support_dir):
    """Download and decompress the XPI file"""

    url = addon_data["xpi_url"]
    file_name = url.split("/")[-1]
    file_path = os.path.join(support_dir, file_name)

    if not os.path.exists(file_path) or os.path.getsize(file_path) < 1:
        print(f"Downloading latest version for {addon_data['name']} ...")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with requests.get(url, stream=True) as response:
            with open(file_path, "wb") as f:
                shutil.copyfileobj(response.raw, f)

    if not os.path.exists(file_path):
        print(f"File is missing and can't be downloaded: {file_name}")
        return

    # If the folder exists and it's not empty, return early
    folder_path = os.path.join(support_dir, addon_data["local_folder"])
    if os.path.isdir(folder_path) and os.listdir(folder_path):
        return

    # Extract the XPI file
    print(f"Extracting {addon_data['version']} for {addon_data['name']}")
    with zipfile.ZipFile(file_path, "r") as z:
        z.extractall(folder_path)


def analyze_locales(addon_data, support_dir):
    """Analyze the list of locale folders in the decompressed add-on"""

    locales_folder = os.path.join(support_dir, addon_data["local_folder"], "_locales")
    locales = []
    if not os.path.isdir(locales_folder) or not os.listdir(locales_folder):
        return locales

    locales = [
        l.replace("_", "-")
        for l in os.listdir(locales_folder)
        if os.path.isdir(os.path.join(locales_folder, l)) and not l.startswith(".")
    ]

    return sorted(locales)


def main():
    # Get absolute path of ../data/metadata.json from the current script location
    root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    json_file = os.path.join(root_path, "data", "metadata.json")
    support_dir = os.path.join(root_path, "support_files")

    with open(json_file) as f:
        addons_metadata = json.load(f)

    for guid_data in addons_metadata.values():
        download_xpi(guid_data, support_dir)
        guid_data["locales"] = analyze_locales(guid_data, support_dir)

    # Write back the updated JSON metadata
    with open(json_file, "w") as f:
        json.dump(addons_metadata, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
