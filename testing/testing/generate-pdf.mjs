
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const htmlPath = path.resolve(
  'playwright-report/index.html'
);

const pdfPath = path.resolve(
  'test-results/TestPilot-AI-Report.pdf'
);

fs.mkdirSync('test-results', { recursive: true });

if (!fs.existsSync(htmlPath)) {
  console.error('HTML report not found');
  process.exit(1);
}

const browser = await chromium.launch({
  headless: true
});

try {
  const page = await browser.newPage();

  await page.goto(pathToFileURL(htmlPath).href, {
    waitUntil: 'networkidle'
  });

  await page.pdf({
    path: pdfPath,
    format: 'A4',
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: '<span></span>',
    footerTemplate: `
      <div style="font-size:8px;width:100%;
      text-align:center">
        TestPilot AI — Automated Test Report
        <span class="pageNumber"></span> /
        <span class="totalPages"></span>
      </div>
    `,
    margin: {
      top: '15mm',
      bottom: '20mm',
      left: '10mm',
      right: '10mm'
    }
  });

  console.log('PDF report generated:', pdfPath);
} finally {
  await browser.close();
}
