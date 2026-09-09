import { readFileSync, readdirSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const walk = directory => readdirSync(directory, { withFileTypes: true }).flatMap(entry => {
  const path = join(directory, entry.name);
  return entry.isDirectory() ? walk(path) : [path];
});
const errors = [];
const check = (condition, message) => { if (!condition) errors.push(message); };
const cssFiles = ['bic-tokens', 'bic-base', 'bic-layout', 'bic-components', 'bic-utilities'];
const styles = cssFiles.map(file => readFileSync(join(root, 'css', `${file}.css`), 'utf8'));
const tokens = new Set([...styles[0].matchAll(/(--bic-[\w-]+)\s*:/g)].map(match => match[1]));
const selectors = new Set([...styles.join('\n').matchAll(/\.([\w-]+)/g)].map(match => match[1]));

for (const path of walk(join(root, 'frontend/src'))) {
  const source = readFileSync(path, 'utf8');
  check(!path.endsWith('.css'), `${path}: keep UI styling in the shared BIC framework`);
  check(!/\bstyle\s*=\s*[{"']|<style\b|\.style(?:\.|\[)/.test(source), `${path}: inline UI styling is not allowed`);
  check(!/#[\da-f]{3,8}\b|\brgba?\(/i.test(source), `${path}: read colors from BIC tokens`);
  check(!/from ['"](?:react-bootstrap|react-toastify)['"]|bootstrap\/dist/.test(source), `${path}: use the BIC components`);
  for (const [, names] of source.matchAll(/className="([^"]*)"/g)) {
    for (const name of names.split(/\s+/).filter(Boolean)) {
      check(selectors.has(name), `${path}: undefined BIC class ${name}`);
    }
  }
}

for (const [index, css] of styles.entries()) {
  if (index > 0) check(!/#[\da-f]{3,8}\b|\brgba?\(/i.test(css), `${cssFiles[index]}: define colors in bic-tokens.css`);
  for (const [, token] of css.matchAll(/var\((--bic-[\w-]+)/g)) {
    check(tokens.has(token), `${cssFiles[index]}: undefined token ${token}`);
  }
}
const entry = readFileSync(join(root, 'frontend/src/main.jsx'), 'utf8');
const imports = [...entry.matchAll(/import ['"]\.\.\/\.\.\/css\/(bic-[\w-]+)\.css['"]/g)].map(match => match[1]);
check(JSON.stringify(imports) === JSON.stringify(cssFiles), 'Import all BIC stylesheets in the documented order');

if (errors.length) {
  console.error(errors.join('\n'));
  process.exitCode = 1;
} else {
  console.log('BIC checks passed: shared classes, tokens, stylesheet order, and no authored inline or legacy UI styles.');
}
