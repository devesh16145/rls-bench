A blog. A post is live when `published_at` is set and in the past, and `unpublish_at` is either unset or in the future. Comments belong to a post.

R1. Anyone, including anonymous visitors, can read live posts.
R2. Authors can read all of their own posts, live or not.
R3. Signed-in users can write posts only as themselves, and can edit and delete only their own posts, without handing a post to another author.
R4. A comment is visible to exactly the people who can read the post it belongs to.
R5. Signed-in users can comment, as themselves, on posts they can read.
R6. Comment authors can delete their own comments, and post authors can delete any comment on their posts. Nobody can edit a comment.
R7. Anonymous visitors cannot write anything.
R8. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
