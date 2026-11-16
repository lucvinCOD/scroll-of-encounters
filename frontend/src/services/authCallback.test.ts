import { test } from "node:test";
import assert from "node:assert/strict";
import { acceptAuthCallback } from "./authCallback.ts";

test("callback removes tokens before exchange, then opens profile", async () => {
  const events: string[] = [];
  const result = await acceptAuthCallback({ pathname: "/", search: "", hash: "#access_token=fixture&refresh_token=fixture-refresh&type=signup" }, (url) => events.push(url), async (tokens) => {
    assert.deepEqual(events, ["/#/entrar"]);
    assert.equal(tokens.access_token, "fixture");
    return { id: "fixture-user", username: "", player_id: null, needs_profile: true };
  });
  assert.equal(result, "/perfil");
});
test("recovery opens password form, errors never retain URL tokens", async () => {
  const location = { pathname: "/", search: "", hash: "#access_token=fixture&refresh_token=fixture-refresh&type=recovery" };
  assert.equal(await acceptAuthCallback(location, () => {}, async () => ({ id: "fixture-user", username: "Test", player_id: 1 })), "/nova-senha");
  const urls: string[] = [];
  assert.equal(await acceptAuthCallback(location, (url) => urls.push(url), async () => { throw new Error("fixture failure"); }), "/entrar?confirmation=failed");
  assert.deepEqual(urls, ["/#/entrar"]);
});
test("normal hash routes do not exchange sessions", async () => {
  assert.equal(await acceptAuthCallback({ pathname: "/", search: "", hash: "#/historico" }, () => assert.fail(), async () => { assert.fail(); }), null);
});
