
import nodemailer from 'nodemailer';
import fs from 'node:fs';

const {
  SMTP_HOST,
  SMTP_PORT,
  SMTP_USER,
  SMTP_PASS,
  EMAIL_FROM,
  EMAIL_TO
} = process.env;

if (!SMTP_HOST || !SMTP_USER || !SMTP_PASS || !EMAIL_TO) {
  console.log('Email settings missing. Skipping notification.');
  process.exit(0);
}

const bugPath = 'test-results/bug-analysis.json';
const summaryPath = 'test-results/ai-summary.json';

const bugs = fs.existsSync(bugPath)
  ? JSON.parse(fs.readFileSync(bugPath, 'utf8'))
  : { totalDetected: 0, failures: [] };

const ai = fs.existsSync(summaryPath)
  ? JSON.parse(fs.readFileSync(summaryPath, 'utf8'))
  : {};

const transporter = nodemailer.createTransport({
  host: SMTP_HOST,
  port: Number(SMTP_PORT || 587),
  secure: Number(SMTP_PORT) === 465,
  auth: {
    user: SMTP_USER,
    pass: SMTP_PASS
  }
});

await transporter.sendMail({
  from: EMAIL_FROM || SMTP_USER,
  to: EMAIL_TO,
  subject: `TestPilot AI: ${bugs.totalDetected} test failures`,
  text: `
TestPilot AI Automated Test Report

Detected failures: ${bugs.totalDetected}

Risk level: ${ai.riskLevel || 'UNKNOWN'}

AI Summary:
${ai.aiSummary || 'See the attached report.'}

Please inspect the GitHub Actions artifacts
for screenshots, traces and complete reports.
  `
});

console.log('Email notification sent.');
