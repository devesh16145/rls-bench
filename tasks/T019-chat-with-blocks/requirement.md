A chat app built with supabase-js. Conversations have participants; users can block other users. Messages are sent with `supabase.from('messages').insert({ conversation_id, sender_id, body }).select()` and edited with `.update({ body }).eq('id', id).select()`.

R1. Users can see the conversations they take part in and every participant of those conversations.
R2. Users can read all messages in conversations they take part in, and no other messages.
R3. Users can send messages, as themselves, into conversations they take part in, unless another participant of that conversation has blocked them.
R4. Senders can edit and delete their own messages. Nobody can edit or delete someone else's message, or move a message to another conversation.
R5. Users can create, see and remove the blocks they made. Nobody can see who has blocked them.
R6. Conversations and participants cannot be created or changed through the app.
R7. Anonymous visitors cannot see or change anything.
R8. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
