import { apiRequest, API_BASE_URL } from "./api";

export async function loginUser(username, password) {
  const formData = new URLSearchParams();
  formData.set("username", username);
  formData.set("password", password);

  const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: formData.toString(),
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "Login failed. Check your credentials and try again."
    );
  }

  if (!data.access_token) {
    throw new Error("The server did not return an access token.");
  }

  sessionStorage.setItem("access_token", data.access_token);

  try {
    const user = await apiRequest("/api/v1/auth/me");
    return user;
  } catch (error) {
    sessionStorage.removeItem("access_token");
    throw error;
  }
}

export function logoutUser() {
  sessionStorage.removeItem("access_token");
}
