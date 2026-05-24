#!/bin/bash
# Quick test — run this while automate.py is running to verify everything works

BASE="http://localhost:5000"

echo "Testing /ping..."
curl -s "$BASE/ping" | python3 -m json.tool

echo ""
echo "Testing new-lead trigger..."
curl -s -X POST "$BASE/trigger/new-lead" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Lead", "email": "test@example.com", "message": "This is a test submission"}' \
  | python3 -m json.tool

echo ""
echo "Testing new-signup trigger..."
curl -s -X POST "$BASE/trigger/new-signup" \
  -H "Content-Type: application/json" \
  -d '{"email": "newuser@example.com", "plan": "pro"}' \
  | python3 -m json.tool

echo ""
echo "Testing custom trigger..."
curl -s -X POST "$BASE/trigger/custom" \
  -H "Content-Type: application/json" \
  -d '{"event": "file_uploaded", "filename": "invoice_001.pdf", "size_kb": 142}' \
  | python3 -m json.tool

echo ""
echo "All tests done. Check your Slack and email."
