import type { Role, User } from "../types.ts";

export function hasRole(user: User | null, allowed: readonly Role[]): boolean {
  return Boolean(user && !user.needs_profile && allowed.includes(user.role || "USER"));
}

export function governanceLinks(user: User | null): string[] {
  if (hasRole(user, ["ADMIN"])) return ["/moderacao", "/administracao"];
  return hasRole(user, ["MODERATOR"]) ? ["/moderacao"] : [];
}
