#!/bin/bash

# Build and push for amd64
docker build -t averkov/izzy-moonbow:latest .
docker push averkov/izzy-moonbow:latest

echo "amd64 image built and pushed successfully!"
