-- Schéma Supabase pour Idéomès (GitHub Pages + Supabase).
-- À coller et exécuter dans l'éditeur SQL du projet Supabase (Database > SQL Editor).
--
-- Porte le modèle documents(collection, doc_id, data jsonb) déjà utilisé côté FastAPI
-- (api/app/base.py::Document) vers Postgres + Row Level Security, puisqu'il n'y a plus de
-- serveur de confiance pour vérifier les permissions : tout repose sur les policies RLS.

-- ----------------------------------------------------------------------------------------
-- 1. Administrateurs
-- ----------------------------------------------------------------------------------------
create table public.admins (
  email text primary key
);
alter table public.admins enable row level security;
-- Aucune policy : illisible/inscriptible via l'API (anon/authenticated), uniquement via
-- is_admin() ci-dessous (SECURITY DEFINER). Ajouter d'autres admins : exécuter un nouvel
-- `insert into public.admins (email) values ('...');` depuis le SQL Editor.
insert into public.admins (email) values ('admin@geomessen.bf');

create or replace function public.is_admin()
returns boolean
language sql
security definer
set search_path = public
stable
as $$
  select exists (
    select 1 from public.admins a
    where a.email = (auth.jwt() ->> 'email')
  );
$$;
grant execute on function public.is_admin() to anon, authenticated;

-- ----------------------------------------------------------------------------------------
-- 2. Documents (collections : actus, reponses, connexions, config, veille, ...)
-- ----------------------------------------------------------------------------------------
create table public.documents (
  collection   text not null,
  doc_id       text not null,
  data         jsonb not null default '{}'::jsonb,
  version      integer not null default 1,
  modifie_par  text,
  modifie_le   timestamptz not null default now(),
  primary key (collection, doc_id)
);
alter table public.documents enable row level security;
grant select, insert, update, delete on public.documents to anon, authenticated;

-- version/modifie_le/modifie_par gérés côté serveur (le client n'est plus digne de confiance).
create or replace function public.documents_set_meta()
returns trigger
language plpgsql
as $$
begin
  new.modifie_le := now();
  new.modifie_par := auth.uid()::text;
  new.version := case when tg_op = 'INSERT' then 1 else old.version + 1 end;
  return new;
end;
$$;
create trigger trg_documents_set_meta
  before insert or update on public.documents
  for each row execute function public.documents_set_meta();

-- Lecture publique : actus (tout le flux) + config/video (mirrors PUBLIC_COLLECTIONS /
-- PUBLIC_LECTURE de l'actuel api/app/securite.py) + maintenance (les annonces
-- doivent atteindre tous les visiteurs, y compris non connectés). L'écriture des
-- annonces reste réservée à l'administrateur par les policies ci-dessous.
create policy documents_select_public
  on public.documents for select
  to anon, authenticated
  using (
    collection = 'actus'
    or collection = 'maintenance'
    or (collection = 'config' and doc_id = 'video')
  );

-- Lecture : admin voit tout ; un participant connecté voit ses propres reponses/connexions
-- (mirrors PERSONNELLES). Tout le reste (veille/*, config/hermes, ...) retombe en admin-only.
create policy documents_select_own_or_admin
  on public.documents for select
  to authenticated
  using (
    public.is_admin()
    or (collection in ('reponses', 'connexions') and doc_id = auth.uid()::text)
  );

-- Écriture : admin, ou participant sur ses propres documents personnels uniquement.
create policy documents_insert
  on public.documents for insert
  to authenticated
  with check (
    public.is_admin()
    or (collection in ('reponses', 'connexions') and doc_id = auth.uid()::text)
  );

create policy documents_update
  on public.documents for update
  to authenticated
  using (
    public.is_admin()
    or (collection in ('reponses', 'connexions') and doc_id = auth.uid()::text)
  )
  with check (
    public.is_admin()
    or (collection in ('reponses', 'connexions') and doc_id = auth.uid()::text)
  );

create policy documents_delete
  on public.documents for delete
  to authenticated
  using (
    public.is_admin()
    or (collection in ('reponses', 'connexions') and doc_id = auth.uid()::text)
  );

-- ----------------------------------------------------------------------------------------
-- 3. Stockage (images d'actualités, vidéo de contexte) — bucket public, écriture admin only
-- ----------------------------------------------------------------------------------------
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'ideomes-public', 'ideomes-public', true, 209715200,
  array['image/png','image/jpeg','image/webp','image/gif','image/svg+xml',
        'video/mp4','video/webm','application/pdf']
)
on conflict (id) do nothing;

create policy storage_admin_insert on storage.objects for insert to authenticated
  with check (bucket_id = 'ideomes-public' and public.is_admin());
create policy storage_admin_update on storage.objects for update to authenticated
  using (bucket_id = 'ideomes-public' and public.is_admin())
  with check (bucket_id = 'ideomes-public' and public.is_admin());
create policy storage_admin_delete on storage.objects for delete to authenticated
  using (bucket_id = 'ideomes-public' and public.is_admin());
-- Nécessaire pour assets.list() (le listing passe par RLS même sur un bucket public ;
-- seule la lecture directe via l'URL publique l'évite).
create policy storage_admin_select on storage.objects for select to authenticated
  using (bucket_id = 'ideomes-public' and public.is_admin());
