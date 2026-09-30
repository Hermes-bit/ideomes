/* Idéomès : remplace localement les capacités de l'artefact claude.ai (window.claude.use)
   par l'API FastAPI du projet. Le code de l'appli (ideomes.src.html) reste inchangé.
   Identité de développement : ?user=u_awa dans l'URL (ou localStorage "ideomes-dev-user").
   Par défaut : "owner" (administrateur). À remplacer par une vraie connexion avant la mise en ligne. */
(function(){
  const API = (window.IDEOMES_API || "").replace(/\/$/, "");
  const q = new URLSearchParams(location.search).get("user");
  const ls = { get(k){ try{return localStorage.getItem(k)}catch(_){return null} }, set(k,v){ try{localStorage.setItem(k,v)}catch(_){} } };
  if(q) ls.set("ideomes-dev-user", q);
  const UID = ls.get("ideomes-dev-user") || "owner";
  const H = { "X-Dev-User": UID };
  const POLL_MS = 3000;

  async function req(method, path, body){
    const r = await fetch(API + path, { method, headers: body ? {...H, "Content-Type":"application/json"} : H, body: body ? JSON.stringify(body) : undefined });
    if(!r.ok){ const e = new Error("HTTP " + r.status); e.code = r.status===403 ? "permission_denied" : "upstream_error"; throw e; }
    return r.json();
  }
  const docSnap = (id, v) => ({ id, exists: !!(v && v.exists), data: () => v && v.data ? JSON.parse(JSON.stringify(v.data)) : undefined });
  const colSnap = (docs) => ({ docs: docs.map(d => docSnap(d.id, {exists:true, data:d.data})), size: docs.length, empty: !docs.length });

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

  function docRef(path){
    const i = path.indexOf("/"), col = path.slice(0, i), id = path.slice(i + 1);
    const url = `/api/db/doc/${encodeURIComponent(col)}/${encodeURIComponent(id)}`;
    return {
      id, path,
      async get(){ return docSnap(id, await req("GET", url)); },
      async set(data){ await req("PUT", url, {data}); },
      async update(data){ await req("PATCH", url, {data}); },
      async delete(){ await req("DELETE", url); },
      onSnapshot(cb, err){ return poll(() => req("GET", url), v => cb(docSnap(id, v)), err); },
    };
  }
  function colRef(col){
    const url = `/api/db/collection/${encodeURIComponent(col)}`;
    return {
      id: col,
      doc(id){ return docRef(col + "/" + (id || (Date.now().toString(36) + Math.random().toString(36).slice(2, 10)))); },
      async add(data){ const r = await req("POST", url, {data}); return docRef(col + "/" + r.id); },
      async get(){ return colSnap((await req("GET", url)).docs); },
      onSnapshot(cb, err){ return poll(() => req("GET", url).then(r => r.docs), d => cb(colSnap(d)), err); },
    };
  }
  const db = { doc: docRef, collection: colRef };

  const user = {
    async me(){ return req("GET", "/api/me"); },
    async isOwner(){ return (await req("GET", "/api/me")).isOwner; },
    async profiles(ids){ return req("POST", "/api/profiles", {ids}); },
  };

  const assets = {
    async upload(blob, opts){
      const f = new FormData(); f.append("fichier", blob, blob.name || "fichier"); if(opts && opts.type) f.append("type", opts.type);
      const r = await fetch(API + "/api/assets", { method:"POST", headers:H, body:f });
      if(!r.ok) throw Object.assign(new Error("upload"), {code: r.status===413 ? "too_large" : r.status===415 ? "unsupported_type" : "upstream_error"});
      return r.json();
    },
    async list(){ return req("GET", "/api/assets"); },
    async delete(ref){ return req("DELETE", "/api/assets/" + String(ref).split("/").pop()); },
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
  window.claude = { async use(name){
    if(name === "assets") return (await user.isOwner()) ? assets : null;   // comme l'artefact : réservé à l'éditeur
    return caps[name] ?? null;
  } };
  console.info("[Idéomès] mode local, utilisateur :", UID);
})();
