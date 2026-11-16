import { getDrivers } from "./api";

// The backend has no login endpoint yet, so passwords are demo-only.
// The control room uses a fixed account; a driver signs in with the phone number on their backend record.
export const ADMIN = { login: "admin", password: "admin123", name: "Control Room" };
export const DRIVER_PASSWORD = "driver123";
const norm = (s) => s.replace(/\s+/g, "").toLowerCase();

export async function authenticate(role, login, password) {
  if (role === "admin") {
    return norm(login) === ADMIN.login && password === ADMIN.password ? { role, id: "admin", name: ADMIN.name } : null;
  }
  const d = (await getDrivers()).find((x) => x.phone === norm(login));
  return d && password === DRIVER_PASSWORD ? { role, id: d.id, name: d.name } : null;
}
