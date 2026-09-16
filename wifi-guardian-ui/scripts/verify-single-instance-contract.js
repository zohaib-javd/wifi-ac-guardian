/**
 * Release contract for repeat launches on Windows.
 *
 * The portable wrapper must extract each launch independently so Electron's
 * process lock can receive a duplicate launch. main.js must then activate the
 * already-running dashboard instead of creating a second Guardian process.
 */
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const packageJson = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'));
const mainProcess = fs.readFileSync(path.join(root, 'main.js'), 'utf8');

if (packageJson.build?.portable?.unpackDirName !== false) {
  throw new Error('Portable builds must set unpackDirName to false for independent temporary extraction.');
}
if (packageJson.build?.win?.requestedExecutionLevel !== 'asInvoker') {
  throw new Error('Windows builds must use standard-user launch for the configured Windows Runtime all-radio recovery request.');
}

for (const requiredSnippet of [
  'app.requestSingleInstanceLock({ appId:',
  "app.on('second-instance'",
  'showDashboard();',
  'mainWindow.moveTop();',
  'mainWindow.focus();',
]) {
  if (!mainProcess.includes(requiredSnippet)) {
    throw new Error(`Single-instance activation behavior is missing: ${requiredSnippet}`);
  }
}

console.log('[verify:single-instance] Verified portable extraction and existing-window activation contract.');
