import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../lib/api";
import { formatProblem } from "../lib/errors";
import type { Workspace } from "../lib/types";

export function WorkspacesPage() {
  const [items, setItems] = useState<Workspace[]>([]);
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    try {
      setItems(await api.listWorkspaces());
    } catch (err) {
      setError(formatProblem(err));
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <section className="stack">
      <h1>Workspaces</h1>
      <form
        className="row"
        onSubmit={async (e) => {
          e.preventDefault();
          if (!name.trim()) return;
          try {
            await api.createWorkspace(name.trim());
            setName("");
            await load();
          } catch (err) {
            setError(formatProblem(err));
          }
        }}
      >
        <input value={name} placeholder="Workspace name" onChange={(e) => setName(e.target.value)} required />
        <button type="submit">Create Workspace</button>
      </form>

      {error ? <p className="error">{error}</p> : null}

      <ul className="list">
        {items.map((workspace) => (
          <li key={workspace.id}>
            <Link to={`/workspaces/${workspace.id}`}>{workspace.name}</Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
