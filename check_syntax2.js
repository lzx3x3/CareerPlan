const fs = require('fs');
const html = fs.readFileSync('c:/Users/Lenovo/WorkBuddy/20260502085005/career-planner.html', 'utf8');
const m = html.match(/<script>([\s\S]*)<\/script>/);
if (m) {
  try {
    new Function(m[1]);
    console.log('JS Syntax OK');
    // Count function definitions
    const funcs = m[1].match(/function\s+\w+/g) || [];
    console.log('Functions found (' + funcs.length + '):', funcs.join(', '));
    // Check goToStep
    const hasGoToStep = m[1].includes('function goToStep');
    console.log('has goToStep:', hasGoToStep);
    console.log('has goToStep in <script>:', hasGoToStep);
    // Check screen-0 in HTML
    const hasScreen0 = html.includes('id="screen-0"');
    console.log('has screen-0 element:', hasScreen0);
  } catch (e) {
    console.log('SYNTAX ERROR:', e.message);
  }
} else {
  console.log('No <script> tag found');
}
