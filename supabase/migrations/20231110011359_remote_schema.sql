CREATE UNIQUE INDEX unique_user_id_year ON public.dashboards USING btree (user_id, year);

alter table "public"."dashboards" add constraint "unique_user_id_year" UNIQUE using index "unique_user_id_year";


