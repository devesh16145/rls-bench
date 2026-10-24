An employee-pulse app built with supabase-js. Respondents answer or change their answer with `supabase.from('survey_responses').upsert({ survey_id, respondent_id, score, comment }).select()`. Survey owners see results with `supabase.from('survey_results').select()`; individual answers must stay anonymous.

R1. Signed-in users can see every survey. Users can create surveys as their owner and rename their own surveys.
R2. Respondents can create, change and read their own response to any survey, as themselves.
R3. Nobody else can read individual responses, including the survey's owner.
R4. Provide a view `public.survey_results` with exactly the columns `survey_id`, `responses` (number of responses) and `avg_score` (average score rounded to 2 decimals). It shows the surveys the viewer owns, and only those with at least 3 responses.
R5. Anonymous visitors cannot see or change anything, including `survey_results`.
R6. Server-side code using the service role keeps full access, and sees `survey_results` for every survey with at least 3 responses.

RLSBENCH-CANARY-f9002c750838f00b
