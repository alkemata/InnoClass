const API = "http://:8000";

export async function login(username, password) {
  const res = await fetch(`${API}/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username, password }),
  });
  const data = await res.json();
  if (res.ok) localStorage.setItem("token", data.access_token);
  return data;
}

export function getToken() {
  return localStorage.getItem("token");
}
