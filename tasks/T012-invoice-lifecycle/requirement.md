An invoicing app built with supabase-js. Invoices move through the statuses `draft` → `sent` → `paid` or `void`. Users listed in `finance_staff` handle payments. The invoice form saves with `supabase.from('invoices').update({ customer, amount, status }).eq('id', id).select()`: every save sends all three fields, changed or not, and reads the row back. New invoices are created with `.insert({ customer, amount }).select()`.

R1. Users can read the invoices they created. Finance staff can read every invoice.
R2. Users can create invoices only as themselves, and only as drafts.
R3. The creator of a draft invoice can change its customer and amount, and can change its status from `draft` to `sent`. Once an invoice is no longer a draft, nobody can change its customer or amount.
R4. Finance staff can change a `sent` invoice's status to `paid` or `void`. No other status change is allowed, for anyone.
R5. Creators can delete their own draft invoices. No other invoice can be deleted.
R6. Nobody can change who created an invoice.
R7. Users can see whether they themselves are finance staff (their own `finance_staff` row). Nobody can change `finance_staff` through the app.
R8. Anonymous visitors cannot see or change anything.
R9. Server-side code using the service role keeps full access and is not bound by the status rules.

RLSBENCH-CANARY-f9002c750838f00b
