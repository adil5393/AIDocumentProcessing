"use client";

import { useEffect, useState } from "react";
import { isLoggedIn } from "../lib/auth";
import './login.css'
const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isLoggedIn()) {
      window.location.replace("/dashboard");
    }
  }, []);

  const handleLogin = async () => {
    if (!username || !password) {
      setError("Username and password required");
      return;
    }

    setError("");
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.message || "Invalid credentials");
        setLoading(false);
        return;
      }

      localStorage.setItem("token", data.access_token);
      window.location.replace("/dashboard");

    } catch {
      setError("Server not reachable");
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <h2>Document Processor System</h2>

      <input
        placeholder="Username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        disabled={loading}
      />

      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        disabled={loading}
        onKeyDown={(e) => e.key === "Enter" && handleLogin()}
      />

      <button onClick={handleLogin} disabled={loading}>
        {loading ? "Logging in..." : "Login"}
      </button>

      {error && <div className="login-error">{error}</div>}
    </div>
  );
}
