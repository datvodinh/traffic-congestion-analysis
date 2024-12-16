import argparse
import os
import time
from datetime import datetime, timedelta

import httpx
import tqdm


def get_link(
    year: int, start_month: int = 1, end_month: int = 12, limit: int = 10000000
):
    urls = []  # Each URL will query for each month

    for month in range(start_month, end_month + 1):
        if month == 12:
            start_month_date = datetime(year, month, 1).strftime("%Y-%m-%d")
            end_month_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            end_month_date = end_month_date.strftime("%Y-%m-%d")
        else:
            start_month_date = datetime(year, month, 1).strftime("%Y-%m-%d")
            end_month_date = datetime(year, month + 1, 1) - timedelta(days=1)
            end_month_date = end_month_date.strftime("%Y-%m-%d")

        link = f"https://data.cityofchicago.org/resource/sxs8-h27x.csv?$where=time%20BETWEEN%20%27{start_month_date}T00:00:00%27%20AND%20%27{end_month_date}T23:59:59%27&$limit={limit}"
        urls.append(
            (link, year, month)
        )  # Store the URL with year and month for filename creation

    return urls


# Generate curl commands
def generate_file_name_and_url(
    year: int, start_month: int = 1, end_month: int = 12, limit: int = 10000000
):
    urls = get_link(year, start_month, end_month, limit)
    commands = []

    for link, year, month in urls:
        filename = f"data_{year}_{month:02}.csv"
        commands.append((filename, link))

    return commands


def get_all_options():
    options = []

    # Example usage of the function
    for command in generate_file_name_and_url(2021, 9, 12):
        options.append(command)

    for command in generate_file_name_and_url(2022):
        options.append(command)

    for command in generate_file_name_and_url(2023):
        options.append(command)

    for command in generate_file_name_and_url(2024):
        options.append(command)

    return options


def download(file_name: str, url: str):
    with httpx.Client(timeout=1000) as client:
        with client.stream("GET", url) as response:
            response.raise_for_status()  # Ensure we catch errors

            total_size = int(
                response.headers.get("Content-Length", 0)
            )  # Get total file size
            block_size = 1024  # Set the block size for downloading
            progress = tqdm.tqdm(
                total=total_size, unit="iB", unit_scale=True, desc=file_name
            )

            with open(file_name, "wb") as f:
                start_time = time.time()
                downloaded_size = 0

                for chunk in response.iter_bytes(block_size):
                    if chunk:  # Filter out keep-alive chunks
                        f.write(chunk)
                        progress.update(len(chunk))

                        # Calculate speed
                        downloaded_size += len(chunk)
                        elapsed_time = time.time() - start_time
                        speed = (
                            downloaded_size / elapsed_time if elapsed_time > 0 else 0
                        )

                        # Update tqdm bar with speed information
                        progress.set_postfix(speed=f"{speed / 1024:.2f} kB/s")

                progress.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download the data from the City of Chicago"
    )

    parser.add_argument(
        "--folder",
        type=str,
        default=os.getcwd(),
        help="Folder to save the data. Default is the current working directory",
    )

    args = parser.parse_args()

    folder = args.folder

    for filename, url in get_all_options():
        if filename not in [x for x in os.listdir(folder) if x.endswith(".csv")]:
            save_path = os.path.join(folder, filename)
            print(f"Downloading {filename} from {url} to {save_path}")
            if not os.path.exists(save_path):
                download(save_path, url)
            print(
                f"Downloaded {filename} from {url}. Size: {os.path.getsize(save_path) / 1024 / 1024:.2f} MB"
            )
