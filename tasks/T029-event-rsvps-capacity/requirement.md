An events app built with supabase-js. Guests RSVP with `supabase.from('rsvps').insert({ event_id, user_id }).select()` and cancel with `.delete()`. Hosts invite people to private events by inserting into `invites`.

R1. Signed-in users can see public events. Private events are visible only to their host and to invited users.
R2. Signed-in users can create events as their host. Hosts can edit and delete their own events, and an event can never be handed to another host.
R3. Hosts can invite people to their events and remove invitations. Users can see their own invitations, and hosts can see the invitations to their events.
R4. Users can RSVP, as themselves, to events they can see, but only while the event has fewer RSVPs than its capacity. Users can cancel their own RSVPs.
R5. Hosts can see every RSVP to their events. Users can see who else has RSVPed to events they have RSVPed to.
R6. Anonymous visitors cannot see or change anything.
R7. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
