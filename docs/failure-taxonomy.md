# Failure taxonomy

Trap IDs used in `task.yaml` `traps:` and categories the LLM judge returns (spec §7.4). Each trap a task lists must have a `traps/<id>.sql` mutation that a test catches.

## Trap patterns

| id | What goes wrong |
|---|---|
| `weak-with-check` | The `with check` of an insert/update policy is weaker than the access rule, e.g. `with check (true)` or a membership check where the rule needs a role. Lets users move or re-own rows. Note: Postgres reuses `using` as `with check` when the latter is omitted, and also checks updated rows against SELECT policies, so the hole only shows when the new row stays visible to the user (see `docs/log.md`, 2026-10-24). |
| `over-broad-for-all` | One `for all` policy whose `using` is written for reading (e.g. `owner or is_public`) also grants update/delete. |
| `null-owner` | `auth.uid() = owner_id` with a nullable `owner_id`: rows with NULL owner leak through `or` branches or vanish. |
| `ownership-change` | Update policy lets the owner column be changed to another user. |
| `child-leak` | Parent table restricted, child table (comments, attachments) open or checked only against itself. |
| `recursive-policy` | A policy on the membership table queries the membership table → `42P17` infinite recursion. Fix: a `security definer` helper. |
| `forgot-enable` | One of several tables never gets `enable row level security`. |
| `soft-delete-leak` | Read policy ignores `deleted_at`/archived flags. |
| `view-bypass` | A view runs as its owner and bypasses RLS (no `security_invoker = true`, or a deliberate owner-rights view without its own access filter), exposing rows or columns to roles that should not see them. |
| `service-role-broken` | Helper functions or policies that error or deny under `service_role`. |
| `restrictive-vs-permissive` | Task needs `as restrictive`; permissive-only solutions over-grant. |
| `claim-trust` | Trusting a user-editable claim (`user_metadata`) or column instead of the authoritative table. |
| `privilege-escalation` | Users can change the column that grants them power (`is_agent`, `department`, `status`) because the update policy or column grants allow editing their own row freely. |
| `time-window` | Publish/expiry windows checked on one bound only (e.g. `published_at is not null`, or ignoring `expires_at`). |
| `rpc-missing-auth-check` | A `security definer` function performs a privileged write without checking who is calling it. |
| `insert-returning-visibility` | Writes that read the row back (`.insert().select()`, PostgREST `return=representation`) fail because the new row isn't visible under the SELECT policies yet, e.g. a creator who isn't a member of the org they just created, or a helper whose snapshot can't see the row being inserted. |
| `self-join` | Membership insert policy lets users add themselves to any group (often as owner/admin). |
| `last-owner` | The last owner can leave or be removed, orphaning the group. |
| `old-vs-new` | A rule compares the row before and after an update (locked fields, immutable owner); a `with check` alone only sees the new row. Needs a trigger or a security-definer lookup of the old value. |
| `state-transition` | Status changes are not restricted to the allowed transitions and actors. |
| `column-grant-blocks-client` | Column-level `grant update (col)` blocks real client writes that send unchanged columns too (supabase-js upserts and form saves), giving `permission denied`. |
| `private-row-leak` | Rows flagged private are exposed to users who get access through sharing/delegation. |
| `transitive-delegation` | Delegates can create or extend delegations, passing access on. |
| `upsert-needs-update` | `.upsert()` on an existing row needs an UPDATE policy (and SELECT for `.select()`); insert-only policies break saves after the first. |
| `anon-write-spoof` | Anonymous or user inserts can set server-owned columns (status, handled_by) because the insert `with check` is `true`. |
| `anon-vs-authenticated` | Policy written `to authenticated` where the rule includes anonymous visitors (or the reverse). |
| `reference-check` | A write may reference a row the user is not allowed to use (inactive product, unpublished course, patient outside the care team). |
| `mfa-not-enforced` | Rule requires an MFA session (`aal2` claim) but the policy ignores the assurance level. |
| `negative-condition` | A "unless X" rule (blocked users, suspensions) is left out, so the default allow wins. |
| `aggregate-limit` | Count-based limits (free copies, max active loans) are not enforced in the insert check. |
| `bucket-scope` | Storage policies check the path but not `bucket_id`, so the same path in another bucket is writable. |
| `rpc-input-validation` | A security-definer RPC trusts its arguments (negative or zero amounts). |
| `overdraft` | A balance-moving RPC does not check the caller can afford the amount. |
| `upsert-takeover` | An "anyone may write as long as the new row is theirs" policy (`using (true) with check (owner = auth.uid())`) lets users take over rows owned by others, e.g. via `upsert ... on conflict`. |
| `case-sensitivity` | Matching a JWT claim (email) against stored data with `=` when the rule says case doesn't matter. |
| `column-leak` | A secret column (hash, token) is readable because only row-level rules were written; needs column privileges or a view. |
| `skip-level-access` | Access meant for a direct relationship (direct manager) is granted through the whole chain. |
| `foreign-email` | A user-supplied delivery address (alerts, notifications) is not tied to the user's verified email, turning the feature into a way to spam others. |
| `soft-delete-visibility` | Soft delete via `update ... set deleted_at` fails because the SELECT policy hides deleted rows from their owner, and Postgres requires the updated row to stay visible. |
| `k-anonymity` | An aggregate view releases results for groups too small to keep individual answers anonymous. |
| `self-approval` | The person who requested something (purchase order, access) can approve it themselves. |
| `approval-limit` | An approval ignores the approver's spending or authority limit. |
| `duplicate-approval` | The same approver is counted twice towards a multi-person approval. |
| `inheritance-missing` | Access granted on a parent (folder, workspace) does not reach its descendants because the check only looks at the row's direct parent. |
| `sso-not-enforced` | A rule that requires a single-sign-on session (`amr` contains `sso/saml`) is not checked, or only checked on some tables. |
| `lock-bypass` | A checkout/lock is not checked on save, so someone who does not hold the lock can overwrite the document. |
| `date-boundary` | An inclusive date range is checked with `<` instead of `<=` (or `between`), so the first or last day is wrongly refused. |
| `unsafe-url` | User-supplied URLs that are rendered as links are not restricted to a safe scheme, allowing `javascript:` links. |
| `sequence-bypass` | A step that must happen in order (sign after the previous signer) can be taken out of turn. |
| `audit-forgery` | Users can write audit rows directly, so the trail can be faked. |
| `missing-audit` | A rule requires every change to be recorded, but no trigger (or only some code paths) writes the audit row. |
| `owner-column-trust` | Storage access is checked against the `owner` column the uploader sets, instead of the path, so users can write into someone else's folder. |
| `file-type-check` | A rule restricting uploaded file types (e.g. `.pdf` only) is not enforced. |
| `rpc-exposed` | An internal function in `public` is left executable by `anon`/`authenticated` (Supabase grants EXECUTE by default), so anyone can call it through the API. |
| `storage-path` | Storage policy checks the bucket and the user's role but not that the object's folder belongs to a resource the user may write. |

## Outcome categories (judge and metrics)

| category | Meaning |
|---|---|
| `pass` | All tests pass. |
| `leak` | Some user gets more access than the rules allow. The headline security failure. |
| `block` | Some allowed action is denied. |
| `apply-error` | The SQL fails to apply (syntax, missing object, wrong type). |
| `format-error` | No ```sql block or a forbidden statement. |
| `runtime-error` | Applies but a policy errors at query time (e.g. recursion, bad cast). |
