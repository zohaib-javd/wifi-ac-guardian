/**
 * Prevent regressions in the Connection Quality and Protection Engine states.
 *
 * This is intentionally source-level: it checks that the dashboard keeps a
 * zero/full-speed marker inside its rounded card, and that the Protection
 * Engine card renders the three-row Last Recovery / Recovery Details /
 * Connection Status layout (feature 007) rather than a numerical "Next
 * Check" countdown or a raw recovery-attempts counter.
 */
const fs = require('fs');
const path = require('path');

const pagePath = path.resolve(__dirname, '..', 'src', 'app', 'page.tsx');
const page = fs.readFileSync(pagePath, 'utf8');

for (const requiredSnippet of [
  'const clampedPercentage = Math.min(100, Math.max(0, percentage));',
  '"--track-radius": "12px"',
  'calc((100% - (2 * var(--track-radius))) * (var(--percentage) / 100))',
  'calc(var(--track-radius) + (100% - (2 * var(--track-radius))) * (var(--percentage) / 100))',
  'translateX(calc(-1% * var(--percentage)))',
  'const isRecovering = telemetry.recoveryActive === true;',
  'const hasRecoveryHistory = Boolean(telemetry.recoveryStartTime);',
  'Last Recovery',
  'Recovery Details',
  'Connection Status',
  'In Progress...',
  'No events recorded.',
  'None (Session Stable)',
  'Active Monitoring',
  'Connecting...',
  'telemetry.backendInitialized && telemetry.backendError',
]) {
  if (!page.includes(requiredSnippet)) {
    throw new Error(`Dashboard radio-state contract is missing: ${requiredSnippet}`);
  }
}

if (page.includes('connectingDots') || page.includes('".".repeat(')) {
  throw new Error('Recovery presentation must use the loading circle with a single Connecting label, not animated dots.');
}

if (page.includes('Next Check') || page.includes('telemetry.nextCheck') || /\bcountdown\b/.test(page)) {
  throw new Error('Protection Engine card must not show a numerical Next Check countdown; use the breathing Connection Status indicator instead.');
}

if (/\/\s*∞|reconnectAttempts|telemetry\.maxAttempts/.test(page)) {
  throw new Error('Protection Engine card must not show a raw "X / ∞" recovery-attempts counter; use the Recovery Details row instead.');
}

console.log('[verify:dashboard-states] Verified bounded speed marker and three-row Protection Engine contract.');
