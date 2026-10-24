A helpdesk. Every user has a profile. Support agents are the users whose profile has `is_agent = true`. Customers open tickets; agents work on them.

R1. Users can read their own profile, and agents can read every profile.
R2. Users can change their own display name. Nobody can change agent status through the app, including agents themselves.
R3. Customers can read their own tickets; agents can read every ticket.
R4. Signed-in users can open tickets only as themselves, only with status `open`, and without an assigned agent.
R5. Agents can update any ticket. Customers cannot update tickets, not even their own.
R6. Nobody can delete tickets through the app.
R7. Agent status comes only from the profile; nothing in the user's token or user metadata grants it.
R8. Anonymous visitors cannot see or change anything.
R9. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
