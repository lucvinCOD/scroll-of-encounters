import { test } from "node:test";
import assert from "node:assert/strict";
import { governanceLinks, hasRole } from "./permissions.ts";
import type { User } from "../types.ts";

const user: User = { id: "fixture", username: "Teste", player_id: 1, role: "USER", moderated_community_ids: [] };
test("common users and incomplete profiles have no governance navigation", () => {
  assert.deepEqual(governanceLinks(null), []);
  assert.deepEqual(governanceLinks(user), []);
  assert.deepEqual(governanceLinks({ ...user, role: "ADMIN", needs_profile: true }), []);
  assert.equal(hasRole(user, ["MODERATOR", "ADMIN"]), false);
});
test("moderator gets moderation only; admin gets both areas", () => {
  assert.deepEqual(governanceLinks({ ...user, role: "MODERATOR", moderated_community_ids: [1, 2] }), ["/moderacao"]);
  assert.deepEqual(governanceLinks({ ...user, role: "ADMIN" }), ["/moderacao", "/administracao"]);
});
test("next permission snapshot removes revoked navigation", () => {
  assert.equal(hasRole({ ...user, role: "ADMIN" }, ["ADMIN"]), true);
  assert.equal(hasRole(user, ["ADMIN"]), false);
});
