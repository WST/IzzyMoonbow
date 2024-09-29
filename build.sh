#!/bin/bash

# Ensure we're using a builder that supports multi-architecture builds
docker buildx create --name mybuilder --use

# Build and push for amd64
docker buildx build --platform linux/amd64 -t averkov/izzy-moonbow:latest --push .

echo "amd64 image built and pushed successfully!"

# Prune everything
echo "Cleaning up..."

# Remove all unused containers, networks, images (both dangling and unreferenced), and optionally, volumes
docker system prune -af --volumes

# Remove all buildx builders except the default one
docker buildx ls | grep -v default | awk '{print $1}' | xargs -r -I {} docker buildx rm {}

# Prune buildx cache
docker buildx prune -af

echo "Cleanup completed. All unused Docker resources have been removed."
