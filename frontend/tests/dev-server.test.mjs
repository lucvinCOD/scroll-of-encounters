import assert from "node:assert/strict";
import { once } from "node:events";
import { createServer as createHttpServer } from "node:http";
import { test } from "node:test";
import { createServer } from "vite";

test("serve o frontend e encaminha /api ao backend configurado", { timeout: 30_000 }, async () => {
  const previousTarget = process.env.API_PROXY_TARGET;
  const previousBaseUrl = process.env.VITE_API_BASE_URL;
  const receivedPaths = [];
  const backend = createHttpServer((request, response) => {
    receivedPaths.push(request.url);
    response.writeHead(200, { "Content-Type": "application/json" });
    response.end(JSON.stringify({ message: "backend simulado" }));
  });
  let frontend;

  try {
    backend.listen(0, "127.0.0.1");
    await once(backend, "listening");
    process.env.API_PROXY_TARGET = `http://127.0.0.1:${backend.address().port}`;
    process.env.VITE_API_BASE_URL = "/api";
    frontend = await createServer({
      server: { host: "127.0.0.1", port: 0, strictPort: false },
      logLevel: "error",
    });
    await frontend.listen();
    const base = `http://127.0.0.1:${frontend.httpServer.address().port}`;

    const html = await fetch(base);
    assert.equal(html.status, 200);
    assert.match(await html.text(), /<title>Scroll of Encounters<\/title>/);

    const css = await fetch(`${base}/src/index.css?direct`);
    assert.equal(css.status, 200);
    assert.match(await css.text(), /\.bg-stone-950/);

    const response = await fetch(`${base}/api/health?source=test`);
    assert.equal(response.status, 200);
    assert.deepEqual(await response.json(), { message: "backend simulado" });
    assert.deepEqual(receivedPaths, ["/health?source=test"]);

    const service = await frontend.transformRequest("/src/services/api.ts");
    assert.ok(service);
    assert.match(service.code, /"VITE_API_BASE_URL"\s*:\s*"\/api"/);
  } finally {
    if (frontend) await frontend.close();
    if (backend.listening) {
      backend.closeAllConnections();
      await new Promise((resolve, reject) => backend.close((error) => error ? reject(error) : resolve()));
    }
    if (previousTarget === undefined) delete process.env.API_PROXY_TARGET;
    else process.env.API_PROXY_TARGET = previousTarget;
    if (previousBaseUrl === undefined) delete process.env.VITE_API_BASE_URL;
    else process.env.VITE_API_BASE_URL = previousBaseUrl;
  }
});
