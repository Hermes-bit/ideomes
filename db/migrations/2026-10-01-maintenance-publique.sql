-- Rend les annonces de maintenance lisibles par tous les visiteurs.
--
-- Jusqu'ici la collection « maintenance » retombait dans la policy admin-only :
-- l'administrateur pouvait publier une annonce, mais personne d'autre ne la voyait.
-- Les annonces s'adressent justement aux utilisateurs, y compris non connectés.
--
-- L'écriture (insert/update/delete) n'est pas touchée : elle reste réservée à
-- l'administrateur via public.is_admin().
--
-- À exécuter une fois dans Supabase : SQL Editor > New query > Run.

drop policy if exists documents_select_public on public.documents;

create policy documents_select_public
  on public.documents for select
  to anon, authenticated
  using (
    collection = 'actus'
    or collection = 'maintenance'
    or (collection = 'config' and doc_id = 'video')
  );
