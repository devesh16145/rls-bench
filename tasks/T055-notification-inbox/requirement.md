An app's notification inbox built with supabase-js. Notifications are created by server code using the service role. The inbox marks a notification read or unread with `supabase.from('notifications').update({ read_at }).eq('id', id)` and dismisses it with `.delete().eq('id', id)`.

R1. Users can read only their own notifications.
R2. Users can mark their own notifications read or unread (set or clear `read_at`) and delete them. They cannot change anything else about a notification.
R3. Nobody can create notifications through the app, not even for themselves.
R4. Anonymous visitors cannot see or change anything.
R5. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
