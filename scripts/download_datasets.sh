#!/usr/bin/env bash

# Script to download datasets for the project.
# Requirements:
#   - AWS CLI (aws)
#   - git
#   - curl
#   - unzip
# Output directories:
#   - data/sorel-20m/processed-data
#   - data/DikeDataset

set -euo pipefail

# base directory for data
DATA_DIR="data"
SOREL_DIR="$DATA_DIR/sorel-20m"
DIKE_DIR="$DATA_DIR/DikeDataset"

mkdir -p "$SOREL_DIR" "$DATA_DIR"

# Download SOREL-20M processed data
# Using no-sign-request since the bucket is public
if command -v aws >/dev/null 2>&1; then
    echo "Syncing SOREL-20M processed data..."
    aws s3 sync --no-sign-request s3://sorel-20m/09-DEC-2020/processed-data/ "$SOREL_DIR/processed-data" "$@"
else
    echo "aws CLI not found. Please install AWS CLI to download SOREL-20M dataset." >&2
    exit 1
fi

# Download DikeDataset using git clone or curl
if [ -d "$DIKE_DIR" ]; then
    echo "DikeDataset already exists at $DIKE_DIR, skipping download."
else
    if command -v git >/dev/null 2>&1; then
        echo "Cloning DikeDataset..."
        git clone https://github.com/iosifache/DikeDataset "$DIKE_DIR"
    elif command -v curl >/dev/null 2>&1; then
        echo "Downloading DikeDataset archive via curl..."
        curl -L https://github.com/iosifache/DikeDataset/archive/refs/heads/master.zip -o "$DATA_DIR/DikeDataset.zip"
        unzip "$DATA_DIR/DikeDataset.zip" -d "$DATA_DIR"
        mv "$DATA_DIR/DikeDataset-master" "$DIKE_DIR"
        rm "$DATA_DIR/DikeDataset.zip"
    else
        echo "Neither git nor curl found. Install one to download DikeDataset." >&2
        exit 1
    fi
fi

echo "Datasets downloaded to $DATA_DIR."
