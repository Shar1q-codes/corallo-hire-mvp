import { Link, Outlet, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthProvider";

export function AppLayout() {
  const { signOut } = useAuth();
  const navigate = useNavigate();

  return (
    <div>
      <header className="topbar">
        <div>
          <Link to="/workspaces" className="brand">
            HDIS Private Beta
          </Link>
        </div>
        <button
          type="button"
          className="secondary"
          onClick={async () => {
            await signOut();
            navigate("/login");
          }}
        >
          Sign out
        </button>
      </header>
      <main className="container">
        <p className="note">This system does not decide. It surfaces uncertainties to validate.</p>
        <Outlet />
      </main>
    </div>
  );
}
