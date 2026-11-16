import type { User } from "../types.ts";

type Exchange = (tokens: { access_token: string; refresh_token: string }) => Promise<User | undefined>;

// Remove segredos do endereço antes de qualquer chamada de rede ou renderização.
export async function acceptAuthCallback(location: Pick<Location, "hash" | "pathname" | "search">, replace: (url: string) => void, exchange: Exchange): Promise<string | null> {
  const parameters = new URLSearchParams(location.hash.slice(1));
  if (!parameters.has("access_token") && !parameters.has("error")) return null;
  const clean = `${location.pathname}${location.search}`;
  replace(`${clean}#/entrar`);
  const access_token = parameters.get("access_token");
  const refresh_token = parameters.get("refresh_token");
  if (!access_token || !refresh_token || parameters.has("error")) return "/entrar?confirmation=failed";
  try {
    const user = await exchange({ access_token, refresh_token });
    if (!user) return "/entrar?confirmation=failed";
    return parameters.get("type") === "recovery" ? "/nova-senha" : user.needs_profile ? "/perfil" : "/partidas/nova";
  } catch {
    return "/entrar?confirmation=failed";
  }
}
