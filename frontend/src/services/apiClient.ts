export class ApiError extends Error {
  readonly status: number;
  readonly details: unknown;

  constructor(status: number, details?: unknown) {
    super(`A API respondeu com HTTP ${status}.`);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

export function createApiClient(baseUrl: string) {
  const base = baseUrl.trim().replace(/\/+$/, "");

  if (!base) {
    throw new Error("A URL base da API precisa ser informada.");
  }

  async function request<T = unknown>(
    path: string,
    options: RequestInit = {},
  ): Promise<T | undefined> {
    const headers = new Headers(options.headers);
    if (!headers.has("Accept")) {
      headers.set("Accept", "application/json");
    }

    const response = await fetch(`${base}/${path.replace(/^\/+/, "")}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let details: unknown;
      if (response.headers.get("Content-Type")?.includes("application/json")) {
        // Erros de proxy podem ter corpo vazio ou JSON inválido; manter o status HTTP.
        try {
          details = await response.json();
        } catch {
          details = undefined;
        }
      }
      throw new ApiError(response.status, details);
    }

    if (response.status === 204) {
      return undefined;
    }

    return response.json() as Promise<T>;
  }

  return { request };
}
