/** Verify every required Windows release-version surface matches root VERSION. */
const fs = require('fs');
const path = require('path');

const uiRoot = path.resolve(__dirname, '..');
const root = path.resolve(uiRoot, '..');
const version = fs.readFileSync(path.join(root, 'VERSION'), 'utf8').trim();

if (!/^\d+\.\d+\.\d+$/.test(version)) {
  throw new Error(`VERSION must use MAJOR.MINOR.PATCH format; received '${version}'.`);
}

function expectMatch(filePath, pattern, label) {
  const content = fs.readFileSync(filePath, 'utf8');
  const match = content.match(pattern);
  if (!match || match[1] !== version) {
    throw new Error(`${label} must be ${version}: ${filePath}`);
  }
}

const packageJson = JSON.parse(fs.readFileSync(path.join(uiRoot, 'package.json'), 'utf8'));
if (packageJson.version !== version) throw new Error(`package.json must be ${version}.`);

const packageLockPath = path.join(uiRoot, 'package-lock.json');
if (fs.existsSync(packageLockPath)) {
  const packageLock = JSON.parse(fs.readFileSync(packageLockPath, 'utf8'));
  if (packageLock.version !== version) throw new Error(`package-lock.json must be ${version}.`);
}

const releaseJson = JSON.parse(fs.readFileSync(path.join(uiRoot, 'public', 'release.json'), 'utf8'));
if (releaseJson.version !== version) throw new Error(`public/release.json must be ${version}.`);

expectMatch(path.join(uiRoot, 'src', 'lib', 'release.ts'), /RELEASE_VERSION = '([^']+)'/, 'About release version');
expectMatch(path.join(root, 'wifi_ac_guardian_win', '__init__.py'), /__version__ = "([^"]+)"/, 'Backend version');
expectMatch(path.join(root, 'pyproject.toml'), /^version = "([^"]+)"/m, 'pyproject version');
expectMatch(path.join(root, 'setup.py'), /version="([^"]+)"/, 'setup.py version');

console.log(`[verify:version] All release surfaces match v${version}.`);
