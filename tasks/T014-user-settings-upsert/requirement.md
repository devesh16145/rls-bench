A habit-tracking app built with supabase-js. Each user has at most one row in `user_settings`. The settings screen saves with `supabase.from('user_settings').upsert({ user_id, timezone, weekly_goal, reminders_enabled }).select()`, which creates the row on the first save and updates it afterwards, and reads it back.

R1. Users can read only their own settings.
R2. Users can create and change only their own settings row, including through the settings screen's save. A settings row can never be moved to another user.
R3. Users can delete their own settings row to reset to defaults.
R4. Anonymous visitors cannot see or change any settings.
R5. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
