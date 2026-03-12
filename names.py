# That is exactly the kind of heavy lifting this library is built for.
# Generating 100,000 globally unique names definitely justifies the initial memory load.

# To guarantee that absolutely no names are repeated across any of the 100 files,
# the most efficient approach is to generate all 100,000 names into a Python set first.
# A set automatically rejects duplicates. Once we hit our target number, we can slice
# that giant list into chunks of 1,000 and write them to your JSON files.

import json
import random
from names_dataset import NameDataset

# Initialize the dataset
print("Loading the dataset into memory...")
nd = NameDataset()

first_names = list(nd.first_names.keys())
last_names = list(nd.last_names.keys())

# Constants for our batch generation
NUM_FILES = 100
NAMES_PER_FILE = 1000
TOTAL_NAMES = NUM_FILES * NAMES_PER_FILE

unique_names = set()

print(f"Generating {TOTAL_NAMES} unique names. This might take a few seconds...")

# Keep generating until the set contains exactly 100,000 unique entries
while len(unique_names) < TOTAL_NAMES:
    first = random.choice(first_names)
    last = random.choice(last_names)
    unique_names.add(f"{first} {last}")

# Convert the set back to a list so we can slice it into chunks
unique_names_list = list(unique_names)

print("Writing to JSON files...")

# Slice the list and export to JSON
for i in range(NUM_FILES):
    start_index = i * NAMES_PER_FILE
    end_index = start_index + NAMES_PER_FILE
    chunk = unique_names_list[start_index:end_index]

    filename = f"names_{i + 1}.json"

    with open(filename, 'w', encoding='utf-8') as f:
        # indent=4 creates the pretty-printed JSON structure you requested
        json.dump(chunk, f, indent=4, ensure_ascii=False)

print("Success! 100 JSON files have been generated.")