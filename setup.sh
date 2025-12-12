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
echo " Setup complete!"
echo "======================================"

streamlit run dashboard.py
