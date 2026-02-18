# Create test tenants/users for live leakage and storage suites

1. Create two tenants in Supabase auth metadata flow and record:
   - LEAK_TEST_TENANT_A_ID
   - LEAK_TEST_TENANT_B_ID
2. Create one authenticated user per tenant and record:
   - LEAK_TEST_USER_A_ID
   - LEAK_TEST_USER_B_ID
3. Obtain JWTs for both users:
   - USER_A_JWT
   - USER_B_JWT
4. Export required env vars:
   - SUPABASE_DB_URL
   - SUPABASE_URL
   - API_BASE_URL
   - LIVE_DB_LEAKAGE_TESTS=true
   - LIVE_API_TESTS=true
   - LIVE_STORAGE_TESTS=true
5. Run go/no-go:
   - python backend/scripts/run_go_no_go.py
