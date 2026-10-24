A document-management app built with supabase-js. Folders form a tree through `parent_id`. Access is given on a folder through `folder_grants` (read, or edit when `can_edit`), and owning or being granted a folder applies to every folder below it. Writes read the row back with `.select()`.

R1. Users can read a folder and the documents in it if they own that folder or any folder above it, or hold a grant on that folder or any folder above it.
R2. Users can create, edit and delete documents in a folder if they own that folder or a folder above it, or hold an editing grant on it or on a folder above it. A document can only be moved to a folder where the user can edit.
R3. Users can create top-level folders as their owner. Only owners of a folder (or of a folder above it) can create subfolders in it, as their owner, and add or remove grants on it.
R4. Users can see the grants given to them and the grants on folders they own (directly or through a folder above).
R5. Anonymous visitors cannot see or change anything.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
