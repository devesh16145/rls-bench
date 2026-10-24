An expense app. Users upload receipts; `uploaded_by` records who uploaded each one. A nightly job imports receipts from the bank feed, and those rows have no uploader (`uploaded_by` is null).

R1. Users can read, edit and delete the receipts they uploaded.
R2. Users can add receipts only as themselves.
R3. Imported receipts are visible only to server-side code. App users can neither read them nor claim them, and cannot turn their own receipts into imported ones.
R4. Anonymous visitors cannot read or change any receipts.
R5. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
