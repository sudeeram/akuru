import { spawn, spawnSync } from "node:child_process";
import { existsSync, readdirSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
const root = fileURLToPath(new URL("../", import.meta.url));
const nvm = join(homedir(), ".nvm", "versions", "node");
const candidates = [
  process.env.PORTAL_NODE,
  process.execPath,
  ...(existsSync(nvm)
    ? readdirSync(nvm)
        .sort((a, b) => b.localeCompare(a, undefined, { numeric: true }))
        .map((v) => join(nvm, v, "bin", "node"))
    : []),
].filter(Boolean);
const node = candidates.find((path) => {
  const result = spawnSync(path, ["--version"], { encoding: "utf8" });
  const [major, minor] = result.stdout?.trim().replace(/^v/, "").split(".").map(Number) || [];
  return !result.error && (major > 22 || (major === 22 && minor >= 13));
});
if (!node) {
  console.error(
    "Node >=22.13 is required. Install a supported Node release yourself, or set PORTAL_NODE to an existing executable. This script never installs software.",
  );
  process.exit(1);
}
const command = process.argv[2] || "dev";
const scripts = {
  dev: ["node_modules/vinext/dist/cli.js", "dev"],
  build: ["node_modules/vinext/dist/cli.js", "build"],
  start: ["serve-local.mjs"],
  typecheck: ["node_modules/typescript/bin/tsc", "--noEmit"],
  lint: ["node_modules/oxlint/bin/oxlint", "app", "features", "lib"],
};
if (!scripts[command]) {
  console.error("Unknown command:", command);
  process.exit(1);
}
console.log(`Using ${node}`);
const child = spawn(node, [...scripts[command], ...process.argv.slice(3)], {
  cwd: join(root, "frontend"),
  stdio: "inherit",
  env: { ...process.env, PATH: dirname(node) + ":" + process.env.PATH },
});
for (const signal of ["SIGINT", "SIGTERM"]) process.on(signal, () => child.kill(signal));
child.on("exit", (code) => process.exit(code ?? 0));
