// Security floors from the October 2026 Node advisory. Review new release lines
// explicitly; a greater major number alone does not imply a patched runtime.
import { pathToFileURL } from 'node:url';
export const nodeRequirement = 'Node 22.23.4+, 24.22.1+, or 26.12.1+ within those supported release lines';
export function isSupportedNode(version) {
  const match = /^v?(\d+)\.(\d+)\.(\d+)$/.exec(version.trim());
  if (!match) return false;
  const [major, minor, patch] = match.slice(1).map(Number);
  const floor = {22: [23, 4], 24: [22, 1], 26: [12, 1]}[major];
  return !!floor && (minor > floor[0] || (minor === floor[0] && patch >= floor[1]));
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  if (!isSupportedNode(process.version)) {
    console.error(`Unsupported Node ${process.version}. Requires ${nodeRequirement}.`);
    process.exitCode = 1;
  } else console.log(`PASS Node runtime ${process.version}`);
}
