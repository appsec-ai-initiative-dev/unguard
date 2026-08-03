// Runtime-load @postman/aether-icons from node_modules so OneAgent inventories it
// as a software component. Imported via NODE_OPTIONS --require (outside webpack),
// so it's not bundled into the Next.js standalone server bundle.
// RVA then matches it against the malicious-package advisory (Shai-Hulud 2.0,
// MAL-2025-190676 / GMS-2025-245, affected versions 2.23.2-2.23.4).
try {
  require('@postman/aether-icons');
} catch (e) {
  console.error('[tracing] failed to load @postman/aether-icons for component inventory:', e.message);
}

const { NodeTracerProvider } = require('@opentelemetry/sdk-trace-node');
const { Resource } = require('@opentelemetry/resources');
const { SEMRESATTRS_SERVICE_NAME } = require('@opentelemetry/semantic-conventions');
const { registerInstrumentations } = require('@opentelemetry/instrumentation');
const { HttpInstrumentation } = require('@opentelemetry/instrumentation-http');
const { UndiciInstrumentation } = require('@opentelemetry/instrumentation-undici');
const { ConsoleSpanExporter, SimpleSpanProcessor } = require('@opentelemetry/sdk-trace-base');

const provider = new NodeTracerProvider({
  resource: new Resource({
    [SEMRESATTRS_SERVICE_NAME]: 'unguard-frontend',
  }),
});

// Console exporter for debugging - OneAgent bridge should intercept and forward spans
provider.addSpanProcessor(new SimpleSpanProcessor(new ConsoleSpanExporter()));

provider.register();

registerInstrumentations({
  instrumentations: [
    new HttpInstrumentation({
      ignoreIncomingRequestHook: (req) => false,
      ignoreOutgoingRequestHook: (req) => false,
    }),
    new UndiciInstrumentation(),
  ],
});
