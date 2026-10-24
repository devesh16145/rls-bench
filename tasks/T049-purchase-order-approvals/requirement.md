A procurement app built with supabase-js. Requesters create purchase orders with `supabase.from('purchase_orders').insert({...}).select()`. An approver records a decision by inserting into `po_approvals` with `.insert({ po_id, approver_id, decision }).select()`; a PO is decided once it has an approval row. Approvers and their spending limits are listed in `approvers`.

R1. Requesters can see their own purchase orders. Approvers can see every purchase order.
R2. Users can create purchase orders as themselves, and can edit and delete their own purchase orders until they are decided.
R3. An approver can record a decision on a purchase order, as themselves, only if its amount is within their limit and they did not request it themselves.
R4. Decisions can never be changed or deleted. Requesters can see the decisions on their own purchase orders; approvers can see every decision.
R5. Users can see their own row in `approvers`. Nobody can change `approvers` through the app.
R6. Anonymous visitors cannot see or change anything.
R7. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
