A fundraising app built with supabase-js. Donors give with `supabase.from('donations').insert({ campaign_id, donor_id, amount_cents, anonymous, message }).select()`. Organisers read the donations to their campaigns from the view `campaign_donations` (columns `id, campaign_id, amount_cents, message, anonymous, donor_id`), which must exist with that name.

R1. Signed-in users can read every campaign. Users can create campaigns as themselves (active) and can close their own campaigns; nothing else about a campaign changes through the app.
R2. A user can donate to an active campaign as themselves with a positive amount. Donations are never changed or deleted through the app.
R3. Donors can read their own rows in `donations`. Nobody else can read `donations` directly.
R4. The view `campaign_donations` shows an organiser every donation to their own campaigns, with `donor_id` set to null for anonymous donations; a donor sees their own donations in the view with their own id, even the anonymous ones. Nobody sees any other rows in the view.
R5. Anonymous visitors cannot see or change anything. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
