// Executor exclusivo dos testes: PostgreSQL em memória, sem DSN ou conexão remota.
import { PGlite } from "@electric-sql/pglite";
import { createInterface } from "node:readline";

const database = new PGlite();
const input = createInterface({ input: process.stdin, crlfDelay: Infinity });
const respond = (value) => process.stdout.write(`${JSON.stringify(value)}\n`);

try {
    await database.waitReady;
    respond({ ready: true });
    for await (const line of input) {
        try {
            const request = JSON.parse(line);
            if (request.operation === "close") {
                break;
            }
            if (request.operation === "query") {
                const result = await database.query(request.sql, request.parameters ?? []);
                respond({ rows: result.rows });
            } else if (request.operation === "exec") {
                await database.exec(request.sql);
                respond({ ok: true });
            } else {
                throw new Error("Operação de teste desconhecida.");
            }
        } catch (error) {
            respond({ error: error.message, code: error.code ?? null });
        }
    }
} finally {
    input.close();
    await database.close();
}
