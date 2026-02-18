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
    userId: data.user.id,
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
    throw new Error("Users must belong to different tenants.");
  }

  const workspaceId = crypto.randomUUID();
  const jobId = crypto.randomUUID();
  const resumeId = crypto.randomUUID();
  const evaluationId = crypto.randomUUID();
  const artifactId = crypto.randomUUID();
  const auditId = crypto.randomUUID();

  const resumePath =
    `tenant/${userA.tenantId}/workspace/${workspaceId}/resume/${resumeId}/resume_a.txt`;

  const { error: wsError } = await userA.client
    .from("workspaces")
    .insert({
      id: workspaceId,
      tenant_id: userA.tenantId,
      name: "A workspace",
      created_by: userA.userId,
    });
  if (wsError) throw new Error(`workspace insert failed: ${wsError.message}`);
  pass("Tenant A inserted workspace");

  const { error: jobError } = await userA.client
    .from("jobs")
    .insert({
      id: jobId,
      tenant_id: userA.tenantId,
      workspace_id: workspaceId,
      title: "Engineer",
      description: "Role description",
      recruiter_notes: "Non-authoritative context",
      created_by: userA.userId,
    });
  if (jobError) throw new Error(`job insert failed: ${jobError.message}`);
  pass("Tenant A inserted job");

  const { error: resumeError } = await userA.client
    .from("resumes")
    .insert({
      id: resumeId,
      tenant_id: userA.tenantId,
      workspace_id: workspaceId,
      file_object_path: resumePath,
      original_filename: "resume_a.txt",
      mime_type: "text/plain",
      size_bytes: 100,
      extracted_text: null,
      created_by: userA.userId,
    });
  if (resumeError) throw new Error(`resume insert failed: ${resumeError.message}`);
  pass("Tenant A inserted resume");

  const { error: evalError } = await userA.client
    .from("resume_job_evaluations")
    .insert({
      id: evaluationId,
      tenant_id: userA.tenantId,
      workspace_id: workspaceId,
      job_id: jobId,
      resume_id: resumeId,
      status: "created",
      failure_reason_code: null,
      created_by: userA.userId,
    });
  if (evalError) throw new Error(`evaluation insert failed: ${evalError.message}`);
  pass("Tenant A inserted evaluation");

  const { error: artifactError } = await userA.client
    .from("artifacts")
    .insert({
      id: artifactId,
      tenant_id: userA.tenantId,
      workspace_id: workspaceId,
      job_id: jobId,
      resume_id: resumeId,
      evaluation_id: evaluationId,
      artifact_type: "intent_hypotheses",
      schema_version: 1,
      content_json: { items: [{ text: "example hypothesis" }] },
      created_by: userA.userId,
    });
  if (artifactError) throw new Error(`artifact insert failed: ${artifactError.message}`);
  pass("Tenant A inserted artifact");

  const { error: auditError } = await userA.client
    .from("audit_log")
    .insert({
      id: auditId,
      tenant_id: userA.tenantId,
      actor_user_id: userA.userId,
      entity_type: "evaluation",
      entity_id: evaluationId,
      action: "create",
      detail_json: { source: "node_test" },
    });
  if (auditError) throw new Error(`audit insert failed: ${auditError.message}`);
  pass("Tenant A inserted audit log");

  const tables = [
    ["workspaces", workspaceId],
    ["jobs", jobId],
    ["resumes", resumeId],
    ["resume_job_evaluations", evaluationId],
    ["artifacts", artifactId],
    ["audit_log", auditId],
  ];

  for (const [table, id] of tables) {
    const { data, error } = await userB.client.from(table).select("id").eq("id", id);
    if (error) {
      fail(`Tenant B read ${table}: ${error.message}`);
      continue;
    }
    if ((data || []).length !== 0) {
      fail(`Tenant B can read tenant A row from ${table}`);
      continue;
    }
    pass(`Tenant B cannot read tenant A row from ${table}`);
  }

  const { error: crossJobInsertError } = await userB.client
    .from("jobs")
    .insert({
      id: crypto.randomUUID(),
      tenant_id: userB.tenantId,
      workspace_id: workspaceId,
      title: "Cross tenant attempt",
      description: "Must fail",
      recruiter_notes: null,
      created_by: userB.userId,
    });
  if (!crossJobInsertError) {
    fail("Tenant B cross-tenant job insert unexpectedly succeeded");
  } else {
    pass("Tenant B cross-tenant job insert blocked");
  }

  const { error: crossEvalInsertError } = await userB.client
    .from("resume_job_evaluations")
    .insert({
      id: crypto.randomUUID(),
      tenant_id: userB.tenantId,
      workspace_id: workspaceId,
      job_id: jobId,
      resume_id: resumeId,
      status: "created",
      created_by: userB.userId,
    });
  if (!crossEvalInsertError) {
    fail("Tenant B cross-tenant evaluation insert unexpectedly succeeded");
  } else {
    pass("Tenant B cross-tenant evaluation insert blocked");
  }

  const { data: updateData, error: updateError } = await userB.client
    .from("workspaces")
    .update({ name: "B overwrite attempt" })
    .eq("id", workspaceId)
    .select("id");
  if (updateError) {
    pass("Tenant B update of tenant A row blocked with error");
  } else if ((updateData || []).length === 0) {
    pass("Tenant B update of tenant A row affected 0 rows");
  } else {
    fail("Tenant B update of tenant A row unexpectedly affected data");
  }

  const { data: deleteData, error: deleteError } = await userB.client
    .from("jobs")
    .delete()
    .eq("id", jobId)
    .select("id");
  if (deleteError) {
    pass("Tenant B delete of tenant A row blocked with error");
  } else if ((deleteData || []).length === 0) {
    pass("Tenant B delete of tenant A row affected 0 rows");
  } else {
    fail("Tenant B delete of tenant A row unexpectedly affected data");
  }

  const { data: artifactUpdateData, error: artifactUpdateError } = await userA.client
    .from("artifacts")
    .update({ content_json: { mutated: true } })
    .eq("id", artifactId)
    .select("id");
  if (artifactUpdateError) {
    pass("Artifacts update blocked (append-only)");
  } else if ((artifactUpdateData || []).length === 0) {
    pass("Artifacts update blocked (0 rows)");
  } else {
    fail("Artifacts update unexpectedly succeeded");
  }

  const { data: auditDeleteData, error: auditDeleteError } = await userA.client
    .from("audit_log")
    .delete()
    .eq("id", auditId)
    .select("id");
  if (auditDeleteError) {
    pass("Audit log delete blocked (append-only)");
  } else if ((auditDeleteData || []).length === 0) {
    pass("Audit log delete blocked (0 rows)");
  } else {
    fail("Audit log delete unexpectedly succeeded");
  }

  await userA.client.auth.signOut();
  await userB.client.auth.signOut();

  if (process.exitCode && process.exitCode !== 0) {
    console.error("RLS leakage test failed.");
  } else {
    console.log("All RLS leakage tests passed.");
  }
}

main().catch((err) => {
  console.error(`FAIL: ${err.message}`);
  process.exit(1);
});
