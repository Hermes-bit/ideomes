-- Permet d'envoyer une idée sans créer de compte.
--
-- Jusqu'ici, seul un visiteur connecté pouvait écrire ses réponses
-- (doc_id = auth.uid()). Les visiteurs non identifiés étaient renvoyés vers
-- l'écran de connexion, ce qui écartait une partie du public visé.
--
-- Portée volontairement étroite :
--   - INSERT uniquement, jamais SELECT, UPDATE ni DELETE ;
--   - uniquement dans la collection « reponses » ;
--   - uniquement sur des doc_id préfixés « anon- », ce qui empêche d'écrire
--     à la place d'un utilisateur identifié et permet de reconnaître l'origine.
--
-- Un visiteur anonyme ne peut donc ni relire, ni modifier, ni supprimer quoi que
-- ce soit, y compris son propre envoi. Seul l'administrateur lit ces réponses.
--
-- À exécuter une fois dans Supabase : SQL Editor > New query > Run.

drop policy if exists documents_insert_anon_reponses on public.documents;

create policy documents_insert_anon_reponses
  on public.documents for insert
  to anon
  with check (
    collection = 'reponses'
    and doc_id like 'anon-%'
  );
