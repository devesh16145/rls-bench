A document editor built with supabase-js that uses check-out locks. Users lock a document with `supabase.rpc('checkout_document', { p_doc_id })` and save and unlock it with `supabase.rpc('checkin_document', { p_doc_id, p_body })`. Implement them as `public.checkout_document(p_doc_id bigint) returns void` and `public.checkin_document(p_doc_id bigint, p_body text) returns void`.

R1. Users can read the documents they have access to (any row in `doc_access`) and their own access rows.
R2. Documents cannot be created, changed or deleted directly through the app; changes go only through the two functions. Nobody can change `doc_access` through the app.
R3. `checkout_document` locks a document for the caller (`checked_out_by`). It must raise an error and change nothing when the caller has no edit access to it, it does not exist, or someone else has it checked out. Checking out a document you already hold succeeds.
R4. `checkin_document` saves the new body and releases the lock. It must raise an error and change nothing unless the caller currently has the document checked out.
R5. Anonymous visitors cannot see or change anything.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
