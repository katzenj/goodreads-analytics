CREATE UNIQUE INDEX unique_title_author_user ON public.books USING btree (title, author, user_id);

alter table "public"."books" add constraint "unique_title_author_user" UNIQUE using index "unique_title_author_user";


