create table "public"."dashboards" (
    "id" bigint generated by default as identity not null,
    "created_at" timestamp with time zone not null default now(),
    "year" text not null,
    "user_id" bigint,
    "data" json not null
);


alter table "public"."dashboards" enable row level security;

CREATE UNIQUE INDEX dashboards_pkey ON public.dashboards USING btree (id);

alter table "public"."dashboards" add constraint "dashboards_pkey" PRIMARY KEY using index "dashboards_pkey";

alter table "public"."dashboards" add constraint "dashboards_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) not valid;

alter table "public"."dashboards" validate constraint "dashboards_user_id_fkey";


