import { getDrivers } from "./api";

// The backend has no login endpoint yet, so passwords are demo-only.
// The control room signs in with their own name and a shared password; a driver signs in with the phone number on their backend record.
export const ADMIN = { login: "admin", password: "admin123" };
export const DRIVER_PASSWORD = "driver123";
const norm = (s) => s.replace(/\s+/g, "").toLowerCase();

export async function authenticate(role, login, password) {
  if (role === "admin") {
    // Any name with the control-room password; that name is shown in the header beside the role.
    const name = login.trim().replace(/\s+/g, " ");
    return name && password === ADMIN.password ? { role, id: "admin", name: name[0].toUpperCase() + name.slice(1) } : null;
  }
  const d = (await getDrivers()).find((x) => x.phone === norm(login));
  return d && password === DRIVER_PASSWORD ? { role, id: d.id, name: d.name } : null;
}
