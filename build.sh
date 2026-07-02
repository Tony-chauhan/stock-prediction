#!/usr/bin/env bash
# Exit on error
set -o errexit

# Upgrade build tools to prevent compilation errors (like Ninja build failed)
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -r requirements.txt
