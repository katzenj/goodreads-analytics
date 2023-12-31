create table "public"."users" (
    "id" bigint generated by default as identity not null,
    "created_at" timestamp with time zone not null default now(),
    "name" text not null,
    "external_id" bigint not null
);


alter table "public"."users" enable row level security;

CREATE UNIQUE INDEX users_external_id_key ON public.users USING btree (external_id);

CREATE UNIQUE INDEX users_pkey ON public.users USING btree (id);

alter table "public"."users" add constraint "users_pkey" PRIMARY KEY using index "users_pkey";

alter table "public"."users" add constraint "users_external_id_key" UNIQUE using index "users_external_id_key";


