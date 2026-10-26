A team wiki. Spaces and memberships are managed by server-side code. To edit a page, the app first takes a lock by updating `locked_by` to the user and `locked_until` to a time at most 30 minutes ahead, and then saves `title` and `body`; taking the lock and saving can happen in one update. Locks are not released by hand; they expire at `locked_until`.

R1. Members of a space can read its pages and the space row; they can see their own membership rows. Nobody else can see them.
R2. Any change to a page must leave it locked by the user making the change, with a lock that is in the future and at most 30 minutes ahead. A page can only be changed while it is unlocked, locked by the same user, or its lock has expired: nobody can edit or take a page while another member holds a live lock.
R3. Members can create pages in their spaces, unlocked. A page can never be moved to another space, and pages are never deleted through the app.
R4. Nobody can change spaces or memberships through the app.
R5. Anonymous visitors cannot see or change anything. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
