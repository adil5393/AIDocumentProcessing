"use client";

import { useState } from "react";
import { useEffect } from "react";
import { isLoggedIn } from "../lib/auth";



export default function LoginPage() {
    useEffect(() => {
    if (isLoggedIn()) {
        window.location.href = "/dashboard";
    }
    }, []);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleLogin = async () => {
  setError("");

  try {
    const res = await fetch("http://localhost:8000/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });

    const data = await res.json();

    if (!res.ok) {
      setError(data.message || "Login failed");
      return;
    }

    // ✅ SAVE TOKEN
    localStorage.setItem("token", data.access_token);

    // ✅ REDIRECT
    window.location.href = "/dashboard";

  } catch (err) {
    setError("Server not reachable");
  }
};

  return (
    <div style={{ maxWidth: 400, margin: "100px auto" }}>
      <h2>Login</h2>

      <input
        placeholder="Username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
      />
      <br /><br />

      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <br /><br />

      <button onClick={handleLogin}>Login</button>

      {error && <p style={{ color: "red" }}>{error}</p>}
    </div>
  );
}
