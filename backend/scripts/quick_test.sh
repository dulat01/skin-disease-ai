#!/bin/bash
# =============================================================================
# Quick Test - Demonstrates the full flow
# =============================================================================

echo "=== Skin Disease AI - Quick Test ==="
echo ""

BASE_URL="http://localhost:8000/api/v1"
EMAIL="demo_$(date +%s)@test.com"
PASSWORD="Demo1234"

# Check if services are running
echo "1. Checking services..."
if ! curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "   ERROR: Services not running. Start with: docker compose up -d"
    exit 1
fi
echo "   All services are healthy!"

# Register (returns token directly)
echo ""
echo "2. Registering user: $EMAIL"
REGISTER=$(curl -s -X POST "$BASE_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\",\"full_name\":\"Demo User\"}")

# Extract token from registration response
TOKEN=$(echo "$REGISTER" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data['data']['tokens']['access_token'])
" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "   ERROR: Registration failed"
    echo "$REGISTER"
    exit 1
fi
echo "   User registered and logged in!"

# Find test image
TEST_IMG=$(find /home/iliyas/PycharmProjects/diploma/skin-disease-ai/TEST_IMAGES -name "*.png" 2>/dev/null | head -1)

if [ -n "$TEST_IMG" ]; then
    echo ""
    echo "3. Making prediction on: $(basename "$TEST_IMG")"
    PREDICTION=$(curl -s -X POST "$BASE_URL/predictions/" \
        -H "Authorization: Bearer $TOKEN" \
        -F "image=@$TEST_IMG")

    echo ""
    echo "   ========================================="
    echo "   PREDICTION RESULT"
    echo "   ========================================="
    echo "$PREDICTION" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('success') and 'data' in data:
        d = data['data']
        print(f\"   Diagnosis: {d.get('predicted_class', 'N/A')}\")
        conf = d.get('confidence', 0) or 0
        print(f\"   Confidence: {conf*100:.1f}%\")
        malignant = d.get('is_malignant')
        status = 'DANGEROUS - See a doctor!' if malignant else 'Benign (not dangerous)'
        print(f\"   Status: {status}\")
        if d.get('top_predictions'):
            print()
            print('   Top predictions:')
            for p in d['top_predictions'][:3]:
                marker = '[!]' if p.get('is_malignant') else '   '
                print(f\"   {marker} {p['class_name']}: {p['confidence']*100:.1f}%\")
    else:
        print(f\"   Error: {data.get('error', data.get('detail', 'Unknown error'))}\")
except Exception as e:
    print(f'   Parse error: {e}')
    print(f'   Response: {sys.stdin.read()[:200]}')
"
    echo "   ========================================="
else
    echo ""
    echo "3. SKIP: No test images found"
fi

echo ""
echo "4. Getting prediction history..."
HISTORY=$(curl -s "$BASE_URL/predictions/history" \
    -H "Authorization: Bearer $TOKEN")
echo "$HISTORY" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    total = data.get('data', {}).get('total', 0)
    print(f'   Total predictions in history: {total}')
except:
    print('   Could not retrieve history')
"

echo ""
echo "=== Test Complete ==="
echo ""
echo "Try the interactive API docs at:"
echo "  - API Gateway:        http://localhost:8000/docs"
echo "  - Auth Service:       http://localhost:8001/docs"
echo "  - Prediction Service: http://localhost:8002/docs"
echo "  - Admin Service:      http://localhost:8003/docs"
