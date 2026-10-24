A library app built with supabase-js. A loan is active while `returned_on` is empty. Members borrow with `supabase.from('loans').insert({ book_id, borrower_id }).select()` and return a book with `.update({ returned_on }).eq('id', id).select()`.

R1. Signed-in users can see the whole book catalogue. Anonymous visitors cannot.
R2. Members can see their own loans; librarians (users listed in `librarians`) can see every loan.
R3. Members can borrow a book, as themselves, only while the book has a free copy (fewer active loans than `copies`) and only while they have fewer than 3 active loans of their own. New loans are always active.
R4. Members can return their own active loans by setting `returned_on`. Nothing else about a loan can be changed, and a returned loan can no longer be changed at all.
R5. Only librarians can add books or change the catalogue. Nobody can delete loans.
R6. Users can see whether they themselves are a librarian. Nobody can change `librarians` through the app.
R7. Anonymous visitors cannot see or change anything.
R8. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
