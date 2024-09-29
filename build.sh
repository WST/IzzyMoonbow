#!/bin/bash

# Ensure we're using the buildx builder
docker buildx create --name mybuilder --use

# Build and push for amd64
docker buildx build --platform linux/amd64 -t averkov/izzy-moonbow:latest-amd64 --push .

# Build and push for arm64
docker buildx build --platform linux/arm64 -t averkov/izzy-moonbow:latest-arm64 --push .

# Create and push the manifest
docker manifest create averkov/izzy-moonbow:latest \
  --amend averkov/izzy-moonbow:latest-amd64 \
  --amend averkov/izzy-moonbow:latest-arm64

docker manifest push averkov/izzy-moonbow:latest

echo "Multi-arch image built and pushed successfully!"
