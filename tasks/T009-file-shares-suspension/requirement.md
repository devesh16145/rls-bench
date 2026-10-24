A file-sharing app. Every file has one owner. Owners share files with other users through `file_shares`; a share may allow editing and may expire at `expires_at` (no value means it never expires). Accounts can be suspended by staff.

R1. Owners can create files as themselves and can read, rename and delete their own files. A file's owner can never be changed through the app.
R2. A user can read a file shared with them while the share has not expired. If the share allows editing, they can also rename the file.
R3. Users a file is shared with can never delete it.
R4. Owners can see, create, change and remove the shares of their own files. Users can see the shares addressed to them, but not shares addressed to anyone else.
R5. Suspended accounts lose all access to files and shares, including their own files.
R6. Users can read their own account row. Nobody can change accounts through the app.
R7. Anonymous visitors cannot see or change anything.
R8. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
