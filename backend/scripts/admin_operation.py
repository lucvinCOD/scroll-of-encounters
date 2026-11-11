"""Gera SQL de operador para revisão. Nunca conecta ao banco ou executa o SQL."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

ROOT = Path(__file__).resolve().parents[2]


def operation_sql(profile_id: str, operation: str, reason: str) -> str:
    target = UUID(profile_id)
    if target.int == 0 or operation not in {"bootstrap", "grant", "revoke"}:
        raise ValueError("Informe um UUID real e uma operação válida.")
    reason = reason.strip()
    if not 10 <= len(reason) <= 2000:
        raise ValueError("A justificativa deve ter entre 10 e 2000 caracteres.")
    # UUID normalizado e literal SQL escapado; nenhum texto vira comando de shell.
    literal = "E'" + reason.replace("\\", "\\\\").replace("'", "''") + "'"
    enabled = "false" if operation == "revoke" else "true"
    bootstrap = "true" if operation == "bootstrap" else "false"
    return (
        "-- OPERACAO DE PERMISSAO: exige revisao e aprovacao especifica antes de executar.\n"
        "BEGIN;\nSET LOCAL lock_timeout = '5s';\nSET LOCAL statement_timeout = '15s';\n"
        f"SELECT soe_private.manage_admin('{target}'::uuid,{enabled},{literal},{bootstrap});\nCOMMIT;\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile-id", required=True, help="UUID do perfil confirmado pelo operador")
    parser.add_argument("--operation", required=True, choices=["bootstrap", "grant", "revoke"])
    parser.add_argument("--reason", required=True, help="Justificativa sem senhas, tokens ou outros segredos")
    args = parser.parse_args()
    try:
        sql = operation_sql(args.profile_id, args.operation, args.reason)
    except ValueError as error:
        parser.error(str(error))
    directory = ROOT / "supabase/.temp/permission-operations"
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = directory / f"{stamp}_{args.operation}_{uuid4().hex[:8]}.sql"
    with path.open("x", encoding="utf-8") as file:
        file.write(sql)
    print("SQL gerado somente para revisao; nenhuma alteracao executada.")
    print(path)
    print("Depois de confirmar o projeto vinculado e obter aprovacao especifica:")
    print(f'npm.cmd run supabase -- db query --remote --file "{path}" --yes')


if __name__ == "__main__":
    main()
