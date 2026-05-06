// Quick JS syntax check for career-planner.html
// Extracts JS between <script> tags and validates with Node

const fs = require('fs');
const path = require('path');

const html = fs.readFileSync('career-planner.html', 'utf8');

// Extract all script blocks
const scriptRegex = /<script[^>]*>([\s\S]*?)<\/script>/gi;
let match;
let blockNum = 0;
let allOK = true;

while ((match = scriptRegex.exec(html)) !== null) {
  blockNum++;
  const code = match[1];
  try {
    new Function(code);
    console.log(`✅ Script block ${blockNum}: OK`);
  } catch (e) {
    console.log(`❌ Script block ${blockNum}: ${e.message}`);
    allOK = false;
  }
}

if (allOK) {
  console.log(`\n✅ All ${blockNum} script blocks passed syntax check.`);
} else {
  console.log(`\n❌ Some script blocks have errors.`);
  process.exitCode = 1;
}
