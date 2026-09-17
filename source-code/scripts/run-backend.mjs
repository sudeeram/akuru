import { existsSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const backend = resolve(root, "backend");
const python = resolve(backend, ".venv", "bin", "python");

if (!existsSync(python)) {
  console.error("Backend environment is missing. Run the setup steps in backend/README.md.");
  process.exit(1);
}

const commands = {
  dev: ["-m", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"],
  worker: ["-m", "app.workers.document_worker"],
  migrate: ["-m", "alembic", "upgrade", "head"],
  seed: ["-m", "app.seed_catalog"],
  test: ["-m", "pytest", "-q"],
  backup: ["-m", "app.database_maintenance", "backup", ...process.argv.slice(3)],
  "restore-drill": ["-m", "app.database_maintenance", "restore-drill", ...process.argv.slice(3)],
  "contract:generate": ["-m", "app.generate_api_contract"],
  "contract:check": ["-m", "app.generate_api_contract", "--check"],
};
const action = process.argv[2];
if (!commands[action]) {
  console.error(`Unknown backend action: ${action ?? "(missing)"}`);
  process.exit(1);
}

const result = spawnSync(python, commands[action], { cwd: backend, stdio: "inherit" });
process.exit(result.status ?? 1);
