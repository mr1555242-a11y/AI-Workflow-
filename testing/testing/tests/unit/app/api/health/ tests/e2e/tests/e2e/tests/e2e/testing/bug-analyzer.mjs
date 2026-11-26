
import fs from 'node:fs';

const input = 'test-results/results.json';
const output = 'test-results/bug-analysis.json';

if (!fs.existsSync(input)) {
  console.error('Test result file not found');
  process.exitCode = 1;
} else {
  const report = JSON.parse(fs.readFileSync(input, 'utf8'));

  const failures = [];

  function inspect(suites = []) {
    for (const suite of suites) {
      for (const spec of suite.specs || []) {
        for (const test of spec.tests || []) {
          for (const result of test.results || []) {
            if (
              result.status === 'failed' ||
              result.status === 'timedOut' ||
              result.status === 'interrupted'
            ) {
              failures.push({
                title: spec.title,
                file: spec.file,
                status: result.status,
                error: result.error?.message || 'Unknown error',
                duration: result.duration
              });
            }
          }
        }
      }

      inspect(suite.suites || []);
    }
  }

  inspect(report.suites || []);

  const analysis = {
    generatedAt: new Date().toISOString(),
    totalDetected: failures.length,
    failures
  };

  fs.mkdirSync('test-results', { recursive: true });

  fs.writeFileSync(
    output,
    JSON.stringify(analysis, null, 2)
  );

  console.log(`Detected failures: ${failures.length}`);
}
