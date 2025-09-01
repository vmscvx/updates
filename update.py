import os
import sys
import time
import base64
import requests


def get_env(var):
    value = os.getenv(var)
    if value is None:
        print(
            f"Error: Environment variable {var} is not set.", file=sys.stderr)
        sys.exit(1)
    return value


def download_data(url, username, password):
    resp = requests.get(url, auth=(username, password))
    resp.encoding = 'cp1251'
    return resp.text


def check_header(lines, expected_b64):
    if not lines:
        return False
    first_line_b64 = base64.b64encode(lines[0].encode('utf-8')).decode('ascii')
    return first_line_b64 == expected_b64


def process_barcodes(lines):
    barcodes = []
    for line in lines[1:]:
        line = line.rstrip()
        if not line:
            continue
        line = line[:-1]
        parts = line.rsplit(";", 1)
        if len(parts) != 2:
            continue
        vendor_code, barcode = parts
        barcode = barcode.strip()
        candidate = barcode.split(" ", 1)[0]
        if len(candidate) == 13:
            barcodes.append((candidate, vendor_code.split(";")[0]))
    barcodes.sort()

    prev_code = 2000000000000
    delta_lines = []
    for barcode, vendor_code in barcodes:
        delta = str(int(barcode) - prev_code)
        prev_code = int(barcode)
        delta_lines.append(f"{delta};{vendor_code}")

    return [str(int(time.time()))] + delta_lines


def save_lines(lines, filename='data.txt'):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    url = get_env("URL")
    user = get_env("USER")
    password = get_env("PASSWORD")
    header_b64 = get_env("HEADER")

    raw_text = download_data(url, user, password)
    lines = raw_text.splitlines()

    if not check_header(lines, header_b64):
        print("Header mismatch, aborting.", file=sys.stderr)
        sys.exit(2)

    processed = process_barcodes(lines)
    save_lines(processed, "data.txt")


if __name__ == "__main__":
    main()
