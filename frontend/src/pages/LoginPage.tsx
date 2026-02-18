import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthProvider";

export function LoginPage() {
  const { signIn, session } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (session) {
      navigate("/workspaces");
    }
  }, [session, navigate]);

  return (
    <main className="centered">
      <form
        className="card"
        onSubmit={async (e) => {
          e.preventDefault();
          setError(null);
          try {
            await signIn(email, password);
            navigate("/workspaces");
          } catch (err) {
            const message = err instanceof Error ? err.message : "Sign in failed.";
            setError(message);
          }
        }}
      >
        <h1>Sign in</h1>
        <label>
          Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label>
          Password
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </label>
        {error ? <p className="error">{error}</p> : null}
        <button type="submit">Sign in</button>
      </form>
    </main>
  );
}
