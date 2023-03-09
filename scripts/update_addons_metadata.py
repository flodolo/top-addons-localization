#! /usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from urllib.parse import urlencode
import argparse
import csv
import json
import os
import requests

# This script gets a CSV file with the top add-ons from AMO, generated from
# https://sql.telemetry.mozilla.org/queries/90809
#
# It then queries AMO's API to find the latest version of the add-on, and
# store the resulting information in a JSON file.


def get_api_response(page, results):
    # Get a page of results from the API, with addons of type extension ordered
    # by number of users
    base_api_url = "https://addons.mozilla.org/api/v5/addons/search/?type=extension&page_size=50&sort=users&page={}"
    search_params = {
        "type": "extension",
        "page": page,
        "page_size": 50,
    }
    api_url = f"{base_api_url}?{urlencode(search_params)}"

    print(f"Requesting page: {page}")
    data = requests.get(api_url).json()
    for result in data["results"]:
        results[result["guid"]] = result


def main():
    # Read command line input parameters
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv", required=True, dest="csv_file", help="Path to CSV file"
    )
    args = parser.parse_args()

    # Get absolute path of ../data/metadata.json from the current script location
    json_file = os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir, "data", "metadata.json")
    )

    addons_metadata = {}
    with open(args.csv_file) as f:
        reader = csv.DictReader(f)
        for ranking, row in enumerate(reader):
            addons_metadata[row["guid"]] = {
                "ranking": ranking + 1,
                "slug": row["guid"],
            }

    api_results = {}
    api_page = 1
    for guid in list(addons_metadata.keys()):
        # Fetch a new page until the add-on guid is found
        while guid not in api_results and api_page < 5:
            get_api_response(api_page, api_results)
            api_page += 1

        if guid in api_results:
            v = api_results[guid]["current_version"]
            addons_metadata[guid]["version"] = v["version"]
            addons_metadata[guid]["xpi_url"] = v["file"]["url"]
            addons_metadata[guid]["name"] = v["file"]["url"]
            # Update avg daily users, in case it changed from the SQL results
            addons_metadata[guid]["average_daily_users"] = api_results[guid][
                "average_daily_users"
            ]
            addons_metadata[guid]["name"] = api_results[guid]["name"].get("en-US", guid)
            # The folder used to extract the add-on locally is derived from the
            # XPI file, replacing - and . in the name with underscores
            file_name = v["file"]["url"].split("/")[-1].rstrip(".xpi")
            folder_name = file_name.replace("-", "_").replace(".", "_")
            addons_metadata[guid]["local_folder"] = folder_name
        else:
            print(f"Skipping {guid}, not found in API")
            del addons_metadata[guid]

    with open(json_file, "w") as f:
        json.dump(addons_metadata, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
