const fs = require('fs');
const path = require('path');

const apiBase = (process.env.FRONTEND_API_BASE_URL || '').trim().replace(/\/$/, '');
const targetPath = path.join(__dirname, '..', 'static', 'js', 'config.js');
const content = `window.__ATTG_API_BASE__ = ${JSON.stringify(apiBase)};\n`;

fs.writeFileSync(targetPath, content, 'utf8');
console.log(`[config] Wrote ${targetPath} with FRONTEND_API_BASE_URL='${apiBase}'`);
