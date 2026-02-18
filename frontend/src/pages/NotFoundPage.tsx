import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <main className="centered">
      <div className="card stack">
        <h1>Not Found</h1>
        <Link to="/workspaces">Back to workspaces</Link>
      </div>
    </main>
  );
}
