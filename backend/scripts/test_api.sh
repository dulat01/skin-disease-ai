#!/bin/bash
# =============================================================================
# Skin Disease AI - API Test Script
# =============================================================================
# This script tests all major API endpoints

BASE_URL="${BASE_URL:-http://localhost:8000}"
AUTH_URL="$BASE_URL/api/v1/auth"
PRED_URL="$BASE_URL/api/v1/predictions"
ADMIN_URL="$BASE_URL/api/v1/admin"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
PASSED=0
FAILED=0

# Generate unique email for test
TEST_EMAIL="test_$(date +%s)@example.com"
TEST_PASSWORD="TestPass123"

print_header() {
    echo -e "\n${YELLOW}========================================${NC}"
    echo -e "${YELLOW}$1${NC}"
    echo -e "${YELLOW}========================================${NC}"
}

print_test() {
    echo -e "\n${YELLOW}TEST:${NC} $1"
}

print_pass() {
    echo -e "${GREEN}PASS:${NC} $1"
    ((PASSED++))
}

print_fail() {
    echo -e "${RED}FAIL:${NC} $1"
    ((FAILED++))
}

# =============================================================================
# Health Check Tests
# =============================================================================
print_header "Health Check Tests"

print_test "API Gateway Health"
RESPONSE=$(curl -s "$BASE_URL/health")
if echo "$RESPONSE" | grep -q '"status":"healthy"'; then
    print_pass "API Gateway is healthy"
else
    print_fail "API Gateway health check failed"
    echo "$RESPONSE"
fi

print_test "Auth Service Health"
RESPONSE=$(curl -s "http://localhost:8001/health")
if echo "$RESPONSE" | grep -q '"status":"healthy"'; then
    print_pass "Auth Service is healthy"
else
    print_fail "Auth Service health check failed"
fi

print_test "Prediction Service Health"
RESPONSE=$(curl -s "http://localhost:8002/health")
if echo "$RESPONSE" | grep -q '"status":"healthy"'; then
    print_pass "Prediction Service is healthy"
else
    print_fail "Prediction Service health check failed"
fi

print_test "Admin Service Health"
RESPONSE=$(curl -s "http://localhost:8003/health")
if echo "$RESPONSE" | grep -q '"status":"healthy"'; then
    print_pass "Admin Service is healthy"
else
    print_fail "Admin Service health check failed"
fi

# =============================================================================
# Authentication Tests
# =============================================================================
print_header "Authentication Tests"

print_test "User Registration"
RESPONSE=$(curl -s -X POST "$AUTH_URL/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"full_name\":\"Test User\"}")

if echo "$RESPONSE" | grep -q '"success":true'; then
    print_pass "User registration successful"
    USER_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['user']['id'])" 2>/dev/null)
    ACCESS_TOKEN=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['tokens']['access_token'])" 2>/dev/null)
    echo "  User ID: $USER_ID"
else
    print_fail "User registration failed"
    echo "$RESPONSE"
    exit 1
fi

print_test "Get Current User (Protected Endpoint)"
RESPONSE=$(curl -s "$AUTH_URL/me" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$RESPONSE" | grep -q "$TEST_EMAIL"; then
    print_pass "Protected endpoint access successful"
else
    print_fail "Protected endpoint access failed"
    echo "$RESPONSE"
fi

print_test "Invalid Token Rejection"
RESPONSE=$(curl -s "$AUTH_URL/me" \
    -H "Authorization: Bearer invalid_token_here")

if echo "$RESPONSE" | grep -qi 'invalid\|expired\|detail'; then
    print_pass "Invalid token correctly rejected"
else
    print_fail "Invalid token was not rejected"
fi

# =============================================================================
# Prediction Tests
# =============================================================================
print_header "Prediction Tests"

# Find a test image
TEST_IMAGE_DIR="/home/iliyas/PycharmProjects/diploma/skin-disease-ai/TEST_IMAGES"
if [ -d "$TEST_IMAGE_DIR" ]; then
    TEST_IMAGE=$(find "$TEST_IMAGE_DIR" -name "*.png" | head -1)
else
    TEST_IMAGE=""
fi

if [ -n "$TEST_IMAGE" ] && [ -f "$TEST_IMAGE" ]; then
    print_test "Synchronous Prediction"
    RESPONSE=$(curl -s -X POST "$PRED_URL/" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -F "image=@$TEST_IMAGE")

    if echo "$RESPONSE" | grep -q '"predicted_class"'; then
        print_pass "Sync prediction successful"
        PRED_CLASS=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['predicted_class'])" 2>/dev/null)
        CONFIDENCE=$(echo "$RESPONSE" | python3 -c "import sys,json; print(f\"{json.load(sys.stdin)['data']['confidence']*100:.1f}%\")" 2>/dev/null)
        IS_MALIGNANT=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print('DANGEROUS' if d['is_malignant'] else 'Benign')" 2>/dev/null)
        echo "  Predicted: $PRED_CLASS"
        echo "  Confidence: $CONFIDENCE"
        echo "  Status: $IS_MALIGNANT"
    else
        print_fail "Sync prediction failed"
        echo "$RESPONSE"
    fi

    print_test "Asynchronous Prediction"
    RESPONSE=$(curl -s -X POST "$PRED_URL/async" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -F "image=@$TEST_IMAGE")

    if echo "$RESPONSE" | grep -q '"task_id"'; then
        print_pass "Async prediction submitted"
        TASK_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['task_id'])" 2>/dev/null)
        echo "  Task ID: $TASK_ID"

        # Wait for task to complete
        echo "  Waiting for task to complete..."
        sleep 3

        print_test "Check Task Status"
        RESPONSE=$(curl -s "$PRED_URL/task/$TASK_ID" \
            -H "Authorization: Bearer $ACCESS_TOKEN")

        if echo "$RESPONSE" | grep -qi 'success\|completed'; then
            print_pass "Async task completed successfully"
            STATUS=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['status'])" 2>/dev/null)
            echo "  Status: $STATUS"
        elif echo "$RESPONSE" | grep -q '"PENDING"'; then
            print_pass "Task is processing (PENDING)"
        else
            print_fail "Task status check failed"
            echo "$RESPONSE"
        fi
    else
        print_fail "Async prediction submission failed"
        echo "$RESPONSE"
    fi

    print_test "Prediction History"
    RESPONSE=$(curl -s "$PRED_URL/history" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    if echo "$RESPONSE" | grep -q '"items"'; then
        print_pass "Prediction history retrieved"
        TOTAL=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['total'])" 2>/dev/null)
        echo "  Total predictions: $TOTAL"
    else
        print_fail "Prediction history failed"
        echo "$RESPONSE"
    fi
else
    echo -e "${YELLOW}SKIP:${NC} No test images found, skipping prediction tests"
fi

# =============================================================================
# Admin Tests (requires admin user)
# =============================================================================
print_header "Admin Tests"

print_test "Admin Access Denied for Regular User"
RESPONSE=$(curl -s "$ADMIN_URL/dashboard" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$RESPONSE" | grep -q '"Admin access required"'; then
    print_pass "Admin access correctly denied for regular user"
else
    print_fail "Admin access control not working"
    echo "$RESPONSE"
fi

# =============================================================================
# Summary
# =============================================================================
print_header "Test Summary"
echo -e "${GREEN}Passed:${NC} $PASSED"
echo -e "${RED}Failed:${NC} $FAILED"
TOTAL=$((PASSED + FAILED))
echo -e "Total: $TOTAL"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}Some tests failed!${NC}"
    exit 1
fi
