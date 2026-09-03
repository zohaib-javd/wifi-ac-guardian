/**
 * Release contract for backend readiness and Windows startup registration.
 *
 * The dashboard must be created only after Guardian IPC responds. The current
 * standard-user release uses a verified HKCU Run-key entry at sign-in.
 */
const fs = require('fs');
const path = require('path');

const mainPath = path.resolve(__dirname, '..', 'main.js');
const main = fs.readFileSync(mainPath, 'utf8');

for (const requiredSnippet of [
  'const GUARDIAN_READY_TIMEOUT_MS = 20000;',
  'function waitForGuardianReady(',
  'await waitForGuardianReady();',
  "'ADD', WINDOWS_RUN_KEY",
  "'QUERY', WINDOWS_RUN_KEY",
  "app.setLoginItemSettings({ openAtLogin: false",
  "process.argv.includes('--startup')",
]) {
  if (!main.includes(requiredSnippet)) {
    throw new Error(`Backend readiness/startup contract is missing: ${requiredSnippet}`);
  }
}

console.log('[verify:startup-readiness] Verified Guardian readiness gate and standard-user Windows Run-key contract.');
