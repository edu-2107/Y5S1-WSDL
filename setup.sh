#!/bin/bash

echo "======================================"
echo "   OntoMaint Installation Script"
echo "======================================"

echo "→ Building Docker image..."
docker build -t ontomaint .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed."
    exit 1
fi

echo "✔ Docker image built successfully."

echo "======================================"
echo "→ Running ontology initialization..."
docker run --rm ontomaint init

echo "======================================"
echo "→ Listing failures..."
docker run --rm ontomaint failures

echo "======================================"
echo "→ Testing failure impact (example: OverheatingA)..."
docker run --rm ontomaint impact --failure OverheatingA

echo "======================================"
echo "→ Testing corrective actions (example: OverheatingA)..."
docker run --rm ontomaint actions --failure OverheatingA

echo "======================================"
echo "→ Listing critical failures..."
docker run --rm ontomaint critical

echo "======================================"
echo "→ What-if scenario (example: FillerB)..."
docker run --rm ontomaint whatif --machine FillerB

echo "======================================"
echo " Setup complete!"
echo " You can now run more commands manually like:"
echo "   docker run --rm ontomaint impact --failure OverloadB"
echo "   docker run --rm ontomaint actions --failure LabelMisalignmentD"
echo "======================================"
