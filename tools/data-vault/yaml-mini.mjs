// yaml-mini.mjs — minimal YAML parser for the Data Vault model spec subset.
//
// Supports:
//   key: value
//   key:
//     nested: ...
//   - list item                  (block sequences)
//   - { name: x, type: VARCHAR } (flow mappings inside lists)
//   - key: a
//     other: b                   (compact list-of-mappings)
//   "quoted", 'quoted'           (strings)
//   true / false / null / number
//   # comments
//   > multi-line block scalar    (folded)
//   foo: >                       (block scalar shorthand)
//     line 1
//     line 2
//
// NOT supported (raise on unexpected): anchors (&,*), tags (!), '|' literal scalars
// with strict newline preservation, complex flow sequences, etc. Use JSON for those.

const FLOW_VAL_END = new Set([',', '}', ']']);

export function parseYaml(text) {
  if (text.startsWith('{') || text.startsWith('[')) {
    // Allow JSON to pass through cleanly.
    return JSON.parse(text);
  }
  const lines = preprocess(text);
  const { value } = parseBlock(lines, 0, -1);
  return value;
}

function preprocess(text) {
  const out = [];
  for (const raw of text.split(/\r?\n/)) {
    const stripped = stripComment(raw);
    if (stripped.trim() === '') continue;
    const indent = stripped.match(/^ */)[0].length;
    out.push({ indent, text: stripped.slice(indent), raw });
  }
  return out;
}

function stripComment(line) {
  let inStr = null;
  for (let i = 0; i < line.length; i++) {
    const c = line[i];
    if (inStr) {
      if (c === '\\') { i++; continue; }
      if (c === inStr) inStr = null;
    } else {
      if (c === '"' || c === "'") inStr = c;
      else if (c === '#') return line.slice(0, i);
    }
  }
  return line;
}

function parseBlock(lines, idx, parentIndent) {
  if (idx >= lines.length) return { value: null, next: idx };
  const first = lines[idx];
  if (first.indent <= parentIndent) return { value: null, next: idx };

  if (first.text.startsWith('- ') || first.text === '-') {
    return parseSequence(lines, idx, first.indent);
  }
  return parseMapping(lines, idx, first.indent);
}

function parseMapping(lines, start, indent) {
  const obj = {};
  let i = start;
  while (i < lines.length) {
    const cur = lines[i];
    if (cur.indent < indent) break;
    if (cur.indent > indent) throw new Error(`Unexpected indent at line: ${cur.raw}`);

    const colon = findColon(cur.text);
    if (colon === -1) throw new Error(`Expected key:value at line: ${cur.raw}`);
    const key = cur.text.slice(0, colon).trim();
    let rest = cur.text.slice(colon + 1).trim();

    if (rest === '' || rest === '>' || rest === '|') {
      // Block follows on next line(s). Handle '>' folded scalar specially.
      if (rest === '>' || rest === '|') {
        const { value, next } = readBlockScalar(lines, i + 1, indent, rest);
        obj[key] = value;
        i = next;
      } else {
        const { value, next } = parseBlock(lines, i + 1, cur.indent);
        obj[key] = value === null ? null : value;
        i = next;
      }
    } else {
      obj[key] = parseScalarOrFlow(rest);
      i += 1;
    }
  }
  return { value: obj, next: i };
}

function readBlockScalar(lines, start, parentIndent, kind) {
  const parts = [];
  let i = start;
  while (i < lines.length && lines[i].indent > parentIndent) {
    parts.push(lines[i].text);
    i++;
  }
  const folded = kind === '>' ? parts.join(' ') : parts.join('\n');
  return { value: folded, next: i };
}

function parseSequence(lines, start, indent) {
  const arr = [];
  let i = start;
  while (i < lines.length) {
    const cur = lines[i];
    if (cur.indent < indent) break;
    if (cur.indent > indent) throw new Error(`Unexpected indent at line: ${cur.raw}`);
    if (!cur.text.startsWith('-')) break;

    const after = cur.text === '-' ? '' : cur.text.slice(2);

    if (after === '') {
      const { value, next } = parseBlock(lines, i + 1, indent);
      arr.push(value);
      i = next;
    } else if (after.startsWith('{') || after.startsWith('[')) {
      // Flow style on the dash line.
      arr.push(parseFlow(after));
      i += 1;
    } else if (findColon(after) !== -1 && !looksLikeScalar(after)) {
      // Compact list-of-mappings: "- key: value" continues with nested keys at indent+2.
      const baseIndent = cur.indent + 2;
      const synthesized = [{ indent: baseIndent, text: after, raw: cur.raw }];
      let j = i + 1;
      while (j < lines.length && lines[j].indent >= baseIndent) {
        // Stop only on a SIBLING dash at the outer sequence's indent.
        if (lines[j].indent === indent && lines[j].text.startsWith('-')) break;
        synthesized.push(lines[j]);
        j++;
      }
      const { value } = parseMapping(synthesized, 0, baseIndent);
      arr.push(value);
      i = j;
    } else {
      arr.push(parseScalarOrFlow(after));
      i += 1;
    }
  }
  return { value: arr, next: i };
}

function findColon(s) {
  let inStr = null;
  let braces = 0;
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (inStr) {
      if (c === '\\') { i++; continue; }
      if (c === inStr) inStr = null;
    } else {
      if (c === '"' || c === "'") inStr = c;
      else if (c === '{' || c === '[') braces++;
      else if (c === '}' || c === ']') braces--;
      else if (c === ':' && braces === 0 && (i === s.length - 1 || s[i + 1] === ' ' || s[i + 1] === '\t')) return i;
    }
  }
  return -1;
}

function looksLikeScalar(s) {
  // Heuristic: if no top-level colon, it's a scalar.
  return findColon(s) === -1;
}

function parseScalarOrFlow(s) {
  s = s.trim();
  if (s.startsWith('{') || s.startsWith('[')) return parseFlow(s);
  return parseScalar(s);
}

function parseScalar(s) {
  if (s === '' || s === '~' || s === 'null' || s === 'Null' || s === 'NULL') return null;
  if (s === 'true' || s === 'True' || s === 'TRUE') return true;
  if (s === 'false' || s === 'False' || s === 'FALSE') return false;
  if (/^-?\d+$/.test(s)) return parseInt(s, 10);
  if (/^-?\d*\.\d+$/.test(s)) return parseFloat(s);
  if ((s.startsWith('"') && s.endsWith('"')) || (s.startsWith("'") && s.endsWith("'"))) {
    return unquote(s);
  }
  return s;
}

function unquote(s) {
  const inner = s.slice(1, -1);
  if (s[0] === '"') {
    return inner.replace(/\\(.)/g, (_, c) => (c === 'n' ? '\n' : c === 't' ? '\t' : c));
  }
  return inner.replace(/''/g, "'");
}

// --- Flow parser (mini, for { ... } and [ ... ]) ---

function parseFlow(s) {
  const { value, idx } = readFlowValue(s, 0);
  // Allow trailing whitespace only.
  if (s.slice(idx).trim() !== '') {
    throw new Error(`Unexpected trailing content in flow value: ${s.slice(idx)}`);
  }
  return value;
}

function readFlowValue(s, i) {
  i = skipWs(s, i);
  const c = s[i];
  if (c === '{') return readFlowMap(s, i);
  if (c === '[') return readFlowSeq(s, i);
  return readFlowScalar(s, i);
}

function readFlowMap(s, i) {
  const out = {};
  i++; // past {
  i = skipWs(s, i);
  if (s[i] === '}') return { value: out, idx: i + 1 };
  while (i < s.length) {
    i = skipWs(s, i);
    let keyEnd = i;
    let inStr = null;
    while (keyEnd < s.length) {
      const c = s[keyEnd];
      if (inStr) {
        if (c === '\\') { keyEnd += 2; continue; }
        if (c === inStr) inStr = null;
      } else {
        if (c === '"' || c === "'") inStr = c;
        else if (c === ':' && (s[keyEnd + 1] === ' ' || s[keyEnd + 1] === ',' || s[keyEnd + 1] === '}' || keyEnd + 1 === s.length)) break;
      }
      keyEnd++;
    }
    const key = parseScalar(s.slice(i, keyEnd).trim());
    i = keyEnd + 1;
    i = skipWs(s, i);
    const v = readFlowValue(s, i);
    out[key] = v.value;
    i = skipWs(s, v.idx);
    if (s[i] === ',') { i++; continue; }
    if (s[i] === '}') return { value: out, idx: i + 1 };
  }
  throw new Error(`Unterminated flow mapping: ${s}`);
}

function readFlowSeq(s, i) {
  const arr = [];
  i++; // past [
  i = skipWs(s, i);
  if (s[i] === ']') return { value: arr, idx: i + 1 };
  while (i < s.length) {
    const v = readFlowValue(s, i);
    arr.push(v.value);
    i = skipWs(s, v.idx);
    if (s[i] === ',') { i++; i = skipWs(s, i); continue; }
    if (s[i] === ']') return { value: arr, idx: i + 1 };
  }
  throw new Error(`Unterminated flow sequence: ${s}`);
}

function readFlowScalar(s, i) {
  let start = i;
  let inStr = null;
  while (i < s.length) {
    const c = s[i];
    if (inStr) {
      if (c === '\\') { i += 2; continue; }
      if (c === inStr) { inStr = null; i++; continue; }
    } else {
      if (c === '"' || c === "'") { inStr = c; i++; continue; }
      if (FLOW_VAL_END.has(c)) break;
    }
    i++;
  }
  return { value: parseScalar(s.slice(start, i).trim()), idx: i };
}

function skipWs(s, i) {
  while (i < s.length && (s[i] === ' ' || s[i] === '\t')) i++;
  return i;
}
