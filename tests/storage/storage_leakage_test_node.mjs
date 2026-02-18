import { createClient } from "@supabase/supabase-js";
import crypto from "node:crypto";

function requireEnv(name) {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing environment variable: ${name}`);
  }
  return value;
}

function decodeJwtPayload(token) {
  const parts = token.split(".");
  if (parts.length < 2) throw new Error("Invalid JWT");
  return JSON.parse(Buffer.from(parts[1], "base64url").toString("utf8"));
}

async function signInClient({ url, anonKey, email, password }) {
  const client = createClient(url, anonKey, {
    auth: { persistSession: false, autoRefreshToken: false },
  });
  const { data, error } = await client.auth.signInWithPassword({ email, password });
  if (error) throw new Error(`Sign-in failed for ${email}: ${error.message}`);
  const payload = decodeJwtPayload(data.session.access_token);
  return {
    client,
    tenantId: payload.tenant_id,
  };
}

function fail(message) {
  console.error(`FAIL: ${message}`);
  process.exitCode = 1;
}

function pass(message) {
  console.log(`PASS: ${message}`);
}

function isUuid(value) {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value || "");
}

async function main() {
  const SUPABASE_URL = requireEnv("SUPABASE_URL");
  const SUPABASE_ANON_KEY = requireEnv("SUPABASE_ANON_KEY");
  const USER_A_EMAIL = requireEnv("USER_A_EMAIL");
  const USER_A_PASSWORD = requireEnv("USER_A_PASSWORD");
  const USER_B_EMAIL = requireEnv("USER_B_EMAIL");
  const USER_B_PASSWORD = requireEnv("USER_B_PASSWORD");

  const userA = await signInClient({
    url: SUPABASE_URL,
    anonKey: SUPABASE_ANON_KEY,
    email: USER_A_EMAIL,
    password: USER_A_PASSWORD,
  });
  const userB = await signInClient({
    url: SUPABASE_URL,
    anonKey: SUPABASE_ANON_KEY,
    email: USER_B_EMAIL,
    password: USER_B_PASSWORD,
  });

  if (!isUuid(userA.tenantId) || !isUuid(userB.tenantId)) {
    throw new Error("Both users must have UUID tenant_id claims in JWT.");
  }
  if (userA.tenantId === userB.tenantId) {
    throw new Error("Users must be in different tenants.");
  }

  const workspaceId = crypto.randomUUID();
  const resumeId = crypto.randomUUID();
  const pathA = `tenant/${userA.tenantId}/workspace/${workspaceId}/resume/${resumeId}/resume.txt`;
  const fileData = new TextEncoder().encode("tenant-isolated resume content");

  const { error: uploadAError } = await userA.client.storage
    .from("resumes")
    .upload(pathA, fileData, { contentType: "text/plain", upsert: false });
  if (uploadAError) {
    throw new Error(`User A upload failed: ${uploadAError.message}`);
  }
  pass("User A uploaded to own tenant path");

  const { data: downloadAData, error: downloadAError } = await userA.client.storage
    .from("resumes")
    .download(pathA);
  if (downloadAError || !downloadAData) {
    fail(`User A download failed: ${downloadAError?.message || "no data"}`);
  } else {
    pass("User A can download own file");
  }

  const { data: downloadBData, error: downloadBError } = await userB.client.storage
    .from("resumes")
    .download(pathA);
  if (!downloadBError && downloadBData) {
    fail("User B unexpectedly downloaded User A file");
  } else {
    pass("User B cannot download User A file");
  }

  const { data: listBData, error: listBError } = await userB.client.storage
    .from("resumes")
    .list(`tenant/${userA.tenantId}`, { limit: 10 });
  if (listBError) {
    pass("User B list of User A prefix blocked");
  } else if ((listBData || []).length === 0) {
    pass("User B list of User A prefix returned 0 rows");
  } else {
    fail("User B list returned User A objects");
  }

  const forbiddenPath = `tenant/${userA.tenantId}/workspace/${crypto.randomUUID()}/resume/${crypto.randomUUID()}/b_forbidden.txt`;
  const { error: uploadBError } = await userB.client.storage
    .from("resumes")
    .upload(forbiddenPath, new TextEncoder().encode("forbidden"), {
      contentType: "text/plain",
      upsert: false,
    });
  if (!uploadBError) {
    fail("User B upload into User A tenant path unexpectedly succeeded");
  } else {
    pass("User B upload into User A tenant path blocked");
  }

  const { error: cleanupError } = await userA.client.storage.from("resumes").remove([pathA]);
  if (cleanupError) {
    pass("Cleanup remove blocked by append-only storage policy (expected in MVP)");
  } else {
    pass("Cleanup remove succeeded");
  }

  await userA.client.auth.signOut();
  await userB.client.auth.signOut();

  if (process.exitCode && process.exitCode !== 0) {
    console.error("Storage leakage test failed.");
  } else {
    console.log("All storage leakage tests passed.");
  }
}

main().catch((err) => {
  console.error(`FAIL: ${err.message}`);
  process.exit(1);
});
