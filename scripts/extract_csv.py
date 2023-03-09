#! /usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import csv
import json
import os
import sys

# This script creates a CSV file from data/metadata.json


def main():
    # Read command line input parameters
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv", required=True, dest="csv_file", help="Path to output CSV file"
    )
    args = parser.parse_args()

    # Get absolute path of ../data/metadata.json from the current script location
    json_file = os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir, "data", "metadata.json")
    )

    with open(json_file) as f:
        addons_metadata = json.load(f)

    # Get a list of all possible locale codes
    all_locales = []
    for addon_data in addons_metadata.values():
        all_locales += addon_data["locales"]

    all_locales = list(set(all_locales))
    all_locales.sort()

    header = "Add-on|Avg Daily Users|Ranking|GUID|Version|Locales|"
    header += "|".join(all_locales)

    csv_output = [header.split("|")]
    for guid, addon_data in addons_metadata.items():
        addon_row = f"{addon_data['name']}|{addon_data['average_daily_users']}|{addon_data['ranking']}|{guid}|{addon_data['version']}|{len(addon_data['locales'])}|"
        for loc in all_locales:
            addon_row += "X|" if loc in addon_data["locales"] else "|"
        csv_output.append(addon_row.split("|"))

    with open(args.csv_file, "w", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerows(csv_output)


if __name__ == "__main__":
    main()
