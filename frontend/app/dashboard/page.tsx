"use client";

import { useEffect } from "react";
import { isLoggedIn, logout } from "../lib/auth";
import { apiFetch } from "../lib/api";

export default function Dashboard() {

  useEffect(() => {
    // 1️⃣ Guard route
    if (!isLoggedIn()) {
      window.location.href = "/login";
      return;
    }

    // 2️⃣ Call protected backend
    apiFetch("http://localhost:8000/api/me")
      .then((res) => res.json())
      .then((data) => {
        console.log("ME:", data);
      });

  }, []);

  return (
    <div>
      <h1>Dashboard</h1>
      <button onClick={logout}>Logout</button>
    </div>
  );
}
