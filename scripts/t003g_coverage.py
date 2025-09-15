#!/usr/bin/env python3
#!/usr/bin/env python3
import os, re, sys, datetime, argparse

root = os.path.dirname(os.path.dirname(__file__))
matrix = os.path.join(root, 'docs', 'ENDPOINTS_MATRIX.md')
if not os.path.exists(matrix):
    print('Matrix file not found:', matrix, file=sys.stderr)
    sys.exit(1)
with open(matrix, 'r', encoding='utf-8') as fh:
    text = fh.read()

# CLI
parser = argparse.ArgumentParser(description='T-003.G gate coverage')
parser.add_argument('--only-tags', help='Comma separated tags to include (e.g. GATE,OFF)', default='GATE,OFF')
parser.add_argument('--mark-keep-skip', action='store_true', help='Mark KEEP rows as SKIP')
parser.add_argument('--mark-na-noaction', action='store_true', help='Mark N/A rows as NO_ACTION')
args = parser.parse_args()
include_tags = [t.strip().upper() for t in args.only_tags.split(',') if t.strip()]

# Parse matrix rows: capture Method + Path + Tag + canonical marker
rows = []
for line in text.splitlines():
    if not line.strip().startswith('|') or line.strip().startswith('|-'):
        continue
    cols = [c for c in line.split('|')]
    # skip header-like rows with fewer columns
    if len(cols) < 7:
        continue
    # columns: | Domain | Method | Path | Canonical | Tag | Caller | ...
    domain = cols[1].strip()
    method = cols[2].strip()
    path_col = cols[3]
    canonical = cols[4].strip()
    tag_col = cols[5].strip()
    # normalize path (strip backticks and whitespace)
    m = re.search(r'`([^`]+)`', path_col)
    path = m.group(1) if m else path_col.strip()
    path = re.sub(r'\s+', '', path)
    rows.append({'domain': domain, 'method': method, 'path': path, 'tag': tag_col.upper(), 'canonical': canonical, 'raw_line': line})

# Filter rows per CLI: keep ones whose tag intersects include_tags
# Group rows by Method+Path and prefer canonical rows (Canonical column contains a checkmark)
grouped = {}
for r in rows:
    key = (r['method'].upper(), r['path'])
    if key not in grouped:
        grouped[key] = []
    grouped[key].append(r)

selected = []
for key, variants in grouped.items():
    # prefer a canonical row (Canonical column contains a checkmark '✅' or 'YES')
    canonical_row = None
    for v in variants:
        if '✅' in v.get('canonical', '') or v.get('canonical', '').upper() in ('YES','Y','TRUE'):
            canonical_row = v
            break
    row = canonical_row if canonical_row else variants[0]
    tag = row['tag']
    tag_parts = [p.strip().upper() for p in re.split(r'[ /,]+', tag) if p.strip()]
    if any(tp in include_tags for tp in tag_parts):
        selected.append(row)
    else:
        # map KEEP -> SKIP if requested; map N/A -> NO_ACTION if requested
        if args.mark_na_noaction and 'N/A' in tag:
            row['mapped_status'] = 'NO_ACTION (N/A)'
            selected.append(row)
        elif args.mark_keep_skip and 'KEEP' in tag:
            row['mapped_status'] = 'SKIP (KEEP)'
            selected.append(row)
# Build list of rows to check from selected rows
rows_to_check = selected
paths = [r['path'] for r in rows_to_check]
if not paths:
    print('No matching rows found for filter; exiting.')
    sys.exit(0)

# Search workspace for files under lms_backend that contain the path
results = []
for p in paths:
    # find the corresponding row to get any mapped_status
    row = next((r for r in rows_to_check if r['path']==p), None)
    if row and row.get('mapped_status'):
        results.append({'path': p, 'status': row['mapped_status'], 'matched_files': [], 'files_with_decorator': []})
        continue
    # special-case N/A NFT mint: mark NO_ACTION if present in matrix as N/A
    if args.mark_na_noaction and p.strip().lower().startswith('/api/v1/nft'):
        results.append({'path': p, 'status': 'NO_ACTION (N/A)', 'matched_files': [], 'files_with_decorator': []})
        continue

    matched_files = []
    files_with_decorator = []
    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith(('.py', '.txt', '.md')):
                fp = os.path.join(dirpath, fn)
                try:
                    data = open(fp, 'r', encoding='utf-8', errors='ignore').read()
                except Exception:
                    continue
                if p in data:
                    matched_files.append(fp)
                    if 'require_web3_enabled' in data:
                        files_with_decorator.append(fp)
    # require a .py matched file to claim OK (avoid docs-only matches)
    py_matches = [f for f in matched_files if f.endswith('.py')]
    if py_matches:
        if any(f in files_with_decorator for f in py_matches):
            status = 'OK'
        else:
            # No .py matched file contains the decorator. Try hint-map for composed URLs
            # to detect handlers assembled via urls/includes and mark OK_COMPOSED.
            status = 'MISSING'
            hints_file = os.path.join(root, 'scripts', 't003g_hints.py')
            if os.path.exists(hints_file):
                try:
                    import importlib.util
                    spec = importlib.util.spec_from_file_location('t003g_hints', hints_file)
                    hints_mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(hints_mod)
                    # get candidate modules for this path
                    candidates = []
                    try:
                        candidates = hints_mod.candidates_for(p)
                    except Exception:
                        # fallback: read HINT_MAP keys
                        H = getattr(hints_mod, 'HINT_MAP', {})
                        for pattern, mods in H.items():
                            if re.match(pattern, p):
                                candidates = mods
                                break
                    for cand in candidates:
                        cand_fp = os.path.join(root, cand)
                        if os.path.exists(cand_fp):
                            try:
                                data = open(cand_fp, 'r', encoding='utf-8', errors='ignore').read()
                            except Exception:
                                data = ''
                            if 'require_web3_enabled' in data:
                                status = f'OK_COMPOSED (matched by hint: {cand})'
                                # include the candidate module among matched files for traceability
                                if cand_fp not in matched_files:
                                    matched_files.append(cand_fp)
                                if cand_fp not in files_with_decorator:
                                    files_with_decorator.append(cand_fp)
                                break
                except Exception:
                    pass
    else:
        # No literal .py matches. Try hint-map for composed URLs.
        status = 'NO_MATCH'
        # Load hint map if available
        hints_file = os.path.join(root, 'scripts', 't003g_hints.py')
        if os.path.exists(hints_file):
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location('t003g_hints', hints_file)
                hints_mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(hints_mod)
                # get candidate modules for this path
                candidates = []
                try:
                    candidates = hints_mod.candidates_for(p)
                except Exception:
                    # fallback: read HINT_MAP keys
                    H = getattr(hints_mod, 'HINT_MAP', {})
                    for pattern, mods in H.items():
                        if re.match(pattern, p):
                            candidates = mods
                            break
                for cand in candidates:
                    cand_fp = os.path.join(root, cand)
                    if os.path.exists(cand_fp):
                        try:
                            data = open(cand_fp, 'r', encoding='utf-8', errors='ignore').read()
                        except Exception:
                            data = ''
                        if 'require_web3_enabled' in data:
                            status = f'OK_COMPOSED (matched by hint: {cand})'
                            # include the candidate module among matched files for traceability
                            matched_files.append(cand_fp)
                            files_with_decorator.append(cand_fp)
                            break
            except Exception:
                pass
    results.append({
        'path': p,
        'status': status,
        'matched_files': matched_files,
        'files_with_decorator': files_with_decorator,
    })
# Write report
out_lines = []
out_lines.append('T-003.G - Web3 gate coverage check')
out_lines.append('Generated: ' + datetime.datetime.utcnow().isoformat() + 'Z')
out_lines.append('')
out_lines.append('| Path | Status | Matched files count | Files with decorator count |')
out_lines.append('| ---- | ------ | ------------------- | -------------------------- |')
for r in results:
    out_lines.append(f"| `{r['path']}` | {r['status']} | {len(r['matched_files'])} | {len(r['files_with_decorator'])} |")
    if r['matched_files']:
        for f in r['matched_files']:
            mark = ' (has gate)' if f in r['files_with_decorator'] else ''
            out_lines.append(f'- {f}{mark}')
    out_lines.append('')
report = '\n'.join(out_lines)
report_file = '/tmp/t003g_gate_coverage.txt'
open(report_file, 'w', encoding='utf-8').write(report)
print('Wrote report to', report_file)
print(report)
# Also produce a markdown block ready to append to EVIDENCE_LOG.md
md_block = []
md_block.append('### T-003.G - Coverage report for Web3 gate')
md_block.append('')
md_block.append(f'Generated: {datetime.datetime.utcnow().isoformat()}Z')
md_block.append('')
md_block.append(report)
md_text = '\n'.join(md_block)
md_out_file = '/tmp/t003g_evidence_block.md'
open(md_out_file, 'w', encoding='utf-8').write(md_text)
print('Wrote evidence block to', md_out_file)
