#!/bin/bash
"""
Test curl per diagnosticare l'errore 400 nell'API TeoCoin
"""

echo "🧪 Test API TeoCoin Apply Discount"
echo "=================================="

# Test 1: Endpoint senza autenticazione
echo "📡 Test 1: Endpoint disponibilità"
curl -X POST http://127.0.0.1:8000/api/v1/teocoin/apply-discount/ \
  -H "Content-Type: application/json" \
  -d '{}' \
  -w "\nStatus: %{http_code}\n" \
  -s

echo -e "\n"

# Test 2: Con dati minimi
echo "📡 Test 2: Con dati minimi"
curl -X POST http://127.0.0.1:8000/api/v1/teocoin/apply-discount/ \
  -H "Content-Type: application/json" \
  -d '{
    "course_id": "test123",
    "teo_amount": "10.00",
    "discount_percentage": "15.00"
  }' \
  -w "\nStatus: %{http_code}\n" \
  -s

echo -e "\n"

# Test 3: Endpoint info
echo "📡 Test 3: Verifica URL"
curl -X GET http://127.0.0.1:8000/api/v1/teocoin/ \
  -w "\nStatus: %{http_code}\n" \
  -s
