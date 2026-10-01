/* Idéomès : remplace localement les capacités de l'artefact claude.ai (window.claude.use)
   par Supabase (Postgres + Auth + Storage), interrogé directement depuis le navigateur.
   Le code de l'appli (ideomes.src.html) reste inchangé : même interface db/user/assets/downloads.
   Identité : Supabase Auth (lien magique par e-mail). Toute la sécurité repose sur les policies
   RLS côté Supabase (voir db/supabase_schema.sql). Il n'y a plus de serveur de confiance ici. */
(function(){
  const SUPABASE_URL = "__SUPABASE_URL__";
  const SUPABASE_ANON_KEY = "__SUPABASE_ANON_KEY__";
  const BUCKET = "ideomes-public";
  const POLL_MS = 3000;
  const EXT = {"image/png":"png","image/jpeg":"jpg","image/webp":"webp","image/gif":"gif",
               "image/svg+xml":"svg","video/mp4":"mp4","video/webm":"webm","application/pdf":"pdf"};
  const MAX = 200 * 1024 * 1024;

  const sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

  function poll(load, emit, onErr){
    let last = null, stop = false;
    const tick = async () => {
      if(stop) return;
      try{ const v = await load(); const k = JSON.stringify(v); if(k !== last){ last = k; emit(v); } }
      catch(e){ onErr && onErr(e); }
      if(!stop) setTimeout(tick, POLL_MS);
    };
    tick();
    return () => { stop = true; };
  }

  const docSnap = (id, v) => ({ id, exists: !!(v && v.exists), data: () => v && v.data ? JSON.parse(JSON.stringify(v.data)) : undefined });
  const colSnap = (docs) => ({ docs: docs.map(d => docSnap(d.id, {exists:true, data:d.data})), size: docs.length, empty: !docs.length });

  function fuseDeep(base, patch){
    const out = {...(base||{})};
    for(const k in patch){
      const v = patch[k];
      if(v && typeof v === "object" && !Array.isArray(v) && v.__delete__){ delete out[k]; continue; }
      if(v && typeof v === "object" && !Array.isArray(v) && typeof out[k] === "object" && !Array.isArray(out[k])){ out[k] = fuseDeep(out[k], v); }
      else out[k] = v;
    }
    return out;
  }

  function errCode(error){ return error && error.code === "42501" ? "permission_denied" : "upstream_error"; }

  function docRef(path){
    const i = path.indexOf("/"), col = path.slice(0, i), id = path.slice(i + 1);
    async function fetchRow(){
      const { data, error } = await sb.from("documents").select("data").eq("collection", col).eq("doc_id", id).maybeSingle();
      if(error) throw Object.assign(new Error("db"), {code: errCode(error)});
      return { exists: !!data, data: data ? data.data : undefined };
    }
    return {
      id, path,
      async get(){ return docSnap(id, await fetchRow()); },
      async set(data){
        const { error } = await sb.from("documents").upsert({ collection: col, doc_id: id, data }, { onConflict: "collection,doc_id" });
        if(error) throw Object.assign(new Error("db"), {code: errCode(error)});
      },
      async update(patch){
        const cur = await fetchRow();
        await this.set(fuseDeep(cur.data, patch));
      },
      async delete(){
        const { error } = await sb.from("documents").delete().eq("collection", col).eq("doc_id", id);
        if(error) throw Object.assign(new Error("db"), {code: errCode(error)});
      },
      onSnapshot(cb, err){ return poll(fetchRow, v => cb(docSnap(id, v)), err); },
    };
  }

  function colRef(col){
    async function fetchRows(){
      const { data, error } = await sb.from("documents").select("doc_id,data").eq("collection", col);
      if(error) throw Object.assign(new Error("db"), {code: errCode(error)});
      return (data || []).map(r => ({ id: r.doc_id, data: r.data }));
    }
    return {
      id: col,
      doc(id){ return docRef(col + "/" + (id || crypto.randomUUID())); },
      async add(data){
        const id = crypto.randomUUID();
        const { error } = await sb.from("documents").insert({ collection: col, doc_id: id, data });
        if(error) throw Object.assign(new Error("db"), {code: errCode(error)});
        return docRef(col + "/" + id);
      },
      /* Création à identifiant imposé, par une insertion simple. À ne pas
         confondre avec doc(id).set(), qui passe par un upsert : sous RLS,
         PostgreSQL exige alors une policy UPDATE en plus de l'INSERT, ce qu'un
         visiteur anonyme n'a pas. */
      async create(id, data){
        const { error } = await sb.from("documents").insert({ collection: col, doc_id: id, data });
        if(error) throw Object.assign(new Error("db"), {code: errCode(error)});
        return docRef(col + "/" + id);
      },
      async get(){ return colSnap(await fetchRows()); },
      onSnapshot(cb, err){ return poll(fetchRows, d => cb(colSnap(d)), err); },
    };
  }

  const db = { doc: docRef, collection: colRef };

  let cachedAdmin = null;
  async function checkAdmin(){
    if(cachedAdmin !== null) return cachedAdmin;
    const { data, error } = await sb.rpc("is_admin");
    cachedAdmin = !error && !!data;
    return cachedAdmin;
  }

  /* Prenom reel de l'utilisateur, uniquement quand le fournisseur nous en donne un
     (Google renseigne given_name / full_name). Une connexion par lien magique
     n'apporte qu'une adresse e-mail : on renvoie null plutot que de deviner un
     prenom a partir de l'adresse, ce qui donnerait des resultats faux. */
  function prenomDe(u){
    const m = (u && u.user_metadata) || {};
    const brut = m.given_name || m.first_name
      || String(m.full_name || m.name || "").trim().split(/\s+/)[0] || "";
    const p = brut.trim();
    if(p.length < 2 || /[0-9@]/.test(p)) return null;
    return p.charAt(0).toUpperCase() + p.slice(1);
  }

  const user = {
    async me(){
      const { data: { session } } = await sb.auth.getSession();
      if(!session) return { id: null, name: null, avatarUrl: null, isOwner: false };
      const isOwner = await checkAdmin();
      return { id: session.user.id, name: isOwner ? "Administrateur Geomessen" : session.user.email, avatarUrl: null, isOwner, firstName: prenomDe(session.user) };
    },
    async isOwner(){ return (await this.me()).isOwner; },
    async profiles(ids){
      if(!ids || !ids.length) return {};
      const { data, error } = await sb.from("documents").select("doc_id,data").eq("collection", "connexions").in("doc_id", ids);
      if(error) return {};
      const out = {};
      (data || []).forEach(r => { out[r.doc_id] = { id: r.doc_id, name: (r.data || {}).valeur || ("Participant " + r.doc_id.slice(0, 8)), avatarUrl: null }; });
      return out;
    },
  };

  function extFor(ct){ return EXT[ct] || "bin"; }
  function publicUrl(path){
    if(!path) return "";
    if(/^https?:\/\//.test(path)) return path;
    return sb.storage.from(BUCKET).getPublicUrl(path).data.publicUrl;
  }

  const assets = {
    async upload(blob, opts){
      const ct = (opts && opts.type) || blob.type || "application/octet-stream";
      if(!EXT[ct]) throw Object.assign(new Error("upload"), {code:"unsupported_type"});
      if(!blob.size || blob.size > MAX) throw Object.assign(new Error("upload"), {code:"too_large"});
      const prefix = ct.startsWith("video/") ? "video" : "news";
      const path = `${prefix}/${crypto.randomUUID()}.${extFor(ct)}`;
      const { error } = await sb.storage.from(BUCKET).upload(path, blob, { contentType: ct, upsert: false });
      if(error) throw Object.assign(new Error("upload"), {code:"upstream_error"});
      return { id: path, url: publicUrl(path), sizeBytes: blob.size, contentType: ct };
    },
    async list(){
      const { data, error } = await sb.storage.from(BUCKET).list("", { limit: 1000, sortBy: { column: "created_at", order: "desc" } });
      if(error) return { assets: [], usage: { files: 0, bytes: 0 } };
      const out = [];
      for(const prefix of ["news", "video"]){
        const { data: sub } = await sb.storage.from(BUCKET).list(prefix, { limit: 1000 });
        (sub || []).forEach(f => out.push({
          id: `${prefix}/${f.name}`, url: publicUrl(`${prefix}/${f.name}`),
          contentType: (f.metadata && f.metadata.mimetype) || "", sizeBytes: (f.metadata && f.metadata.size) || 0,
          createdAt: f.created_at || "",
        }));
      }
      return { assets: out, usage: { files: out.length, bytes: out.reduce((a, x) => a + (x.sizeBytes || 0), 0) } };
    },
    async delete(ref){
      const path = String(ref).replace(/^.*\/(news|video)\//, "$1/");
      const { error } = await sb.storage.from(BUCKET).remove([path]);
      if(error) throw Object.assign(new Error("delete"), {code:"upstream_error"});
    },
  };

  const downloads = {
    async save({filename, data}){
      const blob = data instanceof Blob ? data : new Blob([data], {type: "text/plain;charset=utf-8"});
      const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = filename;
      document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 4000);
      return { saved: true };
    },
  };

  const caps = { db, user, assets: null, downloads };
  window.claude = {
    async use(name){
      if(name === "assets") return (await user.isOwner()) ? assets : null;
      return caps[name] ?? null;
    },
    // Construction d'URL publique toujours disponible (pas gatée par isOwner) : les rendus
    // d'images/vidéo dans ideomes.src.html en ont besoin même pour un visiteur non connecté.
    publicUrl,
    auth: sb.auth,
  };

  sb.auth.onAuthStateChange(() => {
    cachedAdmin = null;
    document.dispatchEvent(new Event("ideomes-auth-change"));
  });

  console.info("[Idéomès] mode Supabase");
})();
