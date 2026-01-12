#!/bin/bash
# Deploy script that loads .env before running gradient CLI

# Load environment variables from .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Run gradient deploy with any additional arguments passed to this script
gradient agent deploy "$@"
