create table public.surveys (
  id bigint primary key,
  owner_id uuid not null references auth.users(id),
  title text not null
);

create table public.survey_responses (
  survey_id bigint not null references public.surveys(id),
  respondent_id uuid not null default auth.uid() references auth.users(id),
  score integer not null check (score between 1 and 5),
  comment text,
  primary key (survey_id, respondent_id)
);
