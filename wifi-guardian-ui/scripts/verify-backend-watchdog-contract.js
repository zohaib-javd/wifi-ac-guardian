/** Verify the bounded Guardian backend watchdog contract without launching Electron. */
const fs = require('fs');
const path = require('path');

const mainPath = path.join(__dirname, '..', 'main.js');
const source = fs.readFileSync(mainPath, 'utf8');
for (const required of [
  'GUARDIAN_MAX_RESTART_ATTEMPTS = 5',
  'scheduleGuardianRestart',
  'backendRestartAttempts >= GUARDIAN_MAX_RESTART_ATTEMPTS',
  'await waitForGuardianReady()',
  'if (isQuitting || backendRestartTimer || pythonProcess) return;',
  'if (backendRestartTimer) clearTimeout(backendRestartTimer);',
]) {
  if (!source.includes(required)) throw new Error(`Missing Guardian watchdog contract: ${required}`);
}
console.log('[verify:backend-watchdog] Bounded restart, readiness confirmation, and quit safety verified.');
