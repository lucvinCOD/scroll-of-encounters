import assert from "node:assert/strict";
import { afterEach, mock, test } from "node:test";
import { ApiError, createApiClient } from "./apiClient.ts";

afterEach(() => mock.restoreAll());

test("mantém o prefixo da API e interpreta uma resposta JSON", async () => {
  const fetchMock = mock.method(globalThis, "fetch", async () =>
    Response.json({ message: "ok" }),
  );
  const api = createApiClient("https://api.example.test/v1/");

  assert.deepEqual(await api.request("/games/"), { message: "ok" });
  assert.equal(fetchMock.mock.calls[0].arguments[0], "https://api.example.test/v1/games/");
  const options = fetchMock.mock.calls[0].arguments[1];
  assert.equal(new Headers(options?.headers).get("Accept"), "application/json");
});

test("preserva método, corpo, cabeçalhos e sinal de cancelamento", async () => {
  const fetchMock = mock.method(globalThis, "fetch", async () => Response.json({ ok: true }));
  const controller = new AbortController();
  const body = JSON.stringify({ example: true });

  await createApiClient("/api").request("/example", {
    method: "POST",
    body,
    headers: { "Content-Type": "application/json", Accept: "application/problem+json" },
    signal: controller.signal,
  });

  const options = fetchMock.mock.calls[0].arguments[1];
  assert.equal(options?.method, "POST");
  assert.equal(options?.body, body);
  assert.equal(options?.signal, controller.signal);
  assert.equal(new Headers(options?.headers).get("Accept"), "application/problem+json");
});

test("expõe o status e os detalhes JSON de um erro FastAPI", async () => {
  mock.method(globalThis, "fetch", async () =>
    Response.json({ detail: "Dados inválidos" }, { status: 422 }),
  );

  await assert.rejects(createApiClient("/api").request("/example"), (error) => {
    assert.ok(error instanceof ApiError);
    assert.equal(error.status, 422);
    assert.deepEqual(error.details, { detail: "Dados inválidos" });
    return true;
  });
});

test("mantém o erro HTTP mesmo se o servidor responder HTML", async () => {
  mock.method(globalThis, "fetch", async () =>
    new Response("<h1>Indisponível</h1>", { status: 502 }),
  );

  await assert.rejects(createApiClient("/api").request("/example"), (error) => {
    assert.ok(error instanceof ApiError);
    assert.equal(error.status, 502);
    assert.equal(error.details, undefined);
    return true;
  });
});

test("mantém o status HTTP quando o JSON de erro é inválido", async () => {
  mock.method(globalThis, "fetch", async () =>
    new Response("invalid", { status: 500, headers: { "Content-Type": "application/json" } }),
  );
  await assert.rejects(createApiClient("/api").request("/example"), (error) => {
    assert.ok(error instanceof ApiError);
    assert.equal(error.status, 500);
    return true;
  });
});

test("aceita 204 sem tentar interpretar um corpo JSON", async () => {
  mock.method(globalThis, "fetch", async () => new Response(null, { status: 204 }));
  assert.equal(await createApiClient("/api").request("/example"), undefined);
});

test("propaga falhas de rede sem transformá-las em sucesso", async () => {
  const networkError = new TypeError("Falha de rede simulada");
  mock.method(globalThis, "fetch", async () => { throw networkError; });
  await assert.rejects(createApiClient("/api").request("/example"), networkError);
});

test("rejeita URL base vazia antes de fazer uma requisição", () => {
  assert.throws(() => createApiClient("  "), /URL base/);
});
