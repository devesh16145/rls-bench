A contract-management app built with supabase-js. Each contract has an owner and can be shared with other users. Versions and tags hang off a contract. Writes read the row back with `.select()`.

R1. Owners can create contracts as themselves and read, rename and delete their own contracts. Users can read the contracts shared with them.
R2. A contract's versions and tags are visible to exactly the people who can read the contract.
R3. Owners and the users a contract is shared with can add new versions to it, as themselves. Versions are never edited or deleted.
R4. Only a contract's owner can add or remove its tags and its shares.
R5. Users can see the share rows of the contracts they own and the shares addressed to them.
R6. Anonymous visitors cannot see or change anything.
R7. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
