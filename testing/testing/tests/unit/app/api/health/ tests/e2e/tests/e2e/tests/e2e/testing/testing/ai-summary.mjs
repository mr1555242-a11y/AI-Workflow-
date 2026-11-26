
import fs from 'node:fs';

const bugFile = 'test-results/bug-analysis.json';
const output = 'test-results/ai-summary.json';

if (!fs.existsSync(bugFile)) {
  console.log('Bug analysis unavailable');
  process.exit(0);
}

const bugs = JSON.parse(fs.readFileSync(bugFile, 'utf8'));

const summary = {
  generatedAt: new Date().toISOString(),
  totalFailures: bugs.totalDetected,
  riskLevel:
    bugs.totalDetected === 0 ? 'LOW' :
    bugs.totalDetected <= 3 ? 'MEDIUM' : 'HIGH',
  findings: bugs.failures.map(item => ({
    test: item.title,
    status: item.status,
    possibleCause: item.error,
    suggestedAction:
      'Inspect the failed test, browser trace and application logs.'
  }))
};

let aiStatus = 'rule-based-fallback';

if (process.env.AI_API_URL) {
  try {
    const response = await fetch(process.env.AI_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(process.env.AI_API_KEY
          ? { Authorization: `Bearer ${process.env.AI_API_KEY}` }
          : {})
      },
      body: JSON.stringify({
        task: 'Summarize automated software test results.',
        instructions:
          'Explain failures, likely causes and safe debugging steps. ' +
          'Do not claim unverified root causes.',
        results: summary
      })
    });

    if (!response.ok) {
      throw new Error(`AI endpoint returned ${response.status}`);
    }

    const result = await response.json();

    if (typeof result.summary !== 'string') {
      throw new Error('Expected a summary string');
    }

    summary.aiSummary = result.summary;
    aiStatus = 'ai-generated';
  } catch (error) {
    summary.aiError = error.message;
  }
}

summary.aiStatus = aiStatus;

fs.writeFileSync(
  output,
  JSON.stringify(summary, null, 2)
);

console.log('Test summary generated:', aiStatus);
