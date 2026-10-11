"""Prepare the jobfit-overview Grafana dashboard offline; no Grafana API, never overwrites a file.

Two modes:
- ``append`` (default, unchanged): add the 17 managed panels to the 4-panel infrastructure dashboard.
- ``layout``: re-arrange and relabel an already managed 21-panel dashboard (17 managed + 4 infrastructure)
  into the sections of ``deploy/observability/layout.json``. Only titles, descriptions, legends, units,
  axis bounds, value mappings and grid positions change; UID, panel ids, datasources, PromQL and
  dashboard metadata are preserved. Re-running it on its own output gives the same file.
"""
import argparse
import copy
import json
import re
from pathlib import Path

MARKER = '[jobfit-observability-v1]'
ROOT = Path(__file__).resolve().parents[1]
GRID_WIDTH = 24
INFRA_ROLES = ('cpu', 'ram', 'disk', 'node')
INFRA_LEGENDS = {'cpu': 'CPU Usage', 'ram': 'Memory Usage', 'disk': 'Disk Usage',
                 'node': 'Node Exporter'}
UP_DOWN = [{'type': 'value', 'options': {'0': {'text': 'Down', 'color': 'red', 'index': 0},
                                         '1': {'text': 'Up', 'color': 'green', 'index': 1}}}]


def merge_dashboard(document, panels, datasource):
    result = copy.deepcopy(document)
    dashboard = result.get('dashboard', result)
    if dashboard.get('uid') != 'jobfit-overview':
        raise ValueError('Expected existing jobfit-overview dashboard')
    existing = dashboard.get('panels')
    if not isinstance(existing, list) or not existing:
        raise ValueError('Existing infrastructure panels must be present')
    if any(MARKER in p.get('description', '') for p in existing):
        raise ValueError('Managed panels already present; review instead of appending twice')
    def flatten(items):
        return [p for item in items for p in [item, *flatten(item.get('panels', []))]]
    all_panels = flatten(existing)
    references = [p.get('datasource') for p in all_panels]
    matching = [ref for ref in references if ref == datasource or
                (isinstance(ref, dict) and ref.get('type') == 'prometheus' and ref.get('uid') == datasource)]
    if not matching:
        raise ValueError('Datasource must match an existing Prometheus panel; do not change its UID')
    selected_datasource = copy.deepcopy(matching[0])
    offset = max(p.get('gridPos', {}).get('y', 0) + p.get('gridPos', {}).get('h', 1) for p in all_panels)
    last_id = max(p.get('id', 0) for p in all_panels)
    for index, source in enumerate(panels):
        panel = copy.deepcopy(source)
        panel.update(id=last_id + index + 1, datasource=copy.deepcopy(selected_datasource))
        panel['description'] = MARKER + ' ' + panel.get('description', '')
        panel['gridPos'] = {'x': index % 2 * 12, 'y': offset + index // 2 * 8, 'w': 12, 'h': 8}
        existing.append(panel)
    # All original dashboard metadata, panels and datasource references stay intact.
    return result


def _dashboard(document):
    dashboard = document.get('dashboard', document)
    if not isinstance(dashboard, dict) or dashboard.get('uid') != 'jobfit-overview':
        raise ValueError('Expected existing jobfit-overview dashboard')
    return dashboard


def _exprs(panel) -> list[tuple]:
    return [(t.get('refId'), t.get('expr')) for t in panel.get('targets') or []]


def _infra_role(panel, titles: dict) -> str | None:
    """Identify one unambiguous node_exporter series; a title alone is insufficient evidence."""
    targets = panel.get('targets')
    if not isinstance(targets, list) or len(targets) != 1 or not isinstance(targets[0], dict):
        raise ValueError(f'Ambiguous infrastructure targets in {panel.get("title")!r}')
    target = targets[0]
    if not isinstance(target.get('refId'), str) or not isinstance(target.get('expr'), str):
        raise ValueError(f'Invalid infrastructure target in {panel.get("title")!r}')
    expr = target['expr']
    matches = [role for role, present in (
        ('cpu', 'node_cpu_seconds_total' in expr),
        ('ram', 'node_memory_' in expr),
        ('disk', 'node_filesystem_' in expr),
        ('node', bool(re.search(r'\bup\s*\{[^}]*\bjob\s*=\s*["\']node(?:-exporter)?["\']', expr))),
    ) if present]
    if len(matches) > 1:
        raise ValueError(f'Ambiguous infrastructure PromQL in {panel.get("title")!r}')
    role = matches[0] if matches else None
    if panel.get('title') in titles and role != titles[panel['title']]:
        raise ValueError(f'Infrastructure title and PromQL disagree in {panel.get("title")!r}')
    return role


def _percent_scale(panel) -> tuple[str, int] | None:
    """('percent', 100) for a 0-100 query, ('percentunit', 1) for a 0-1 ratio, None when unknown."""
    expr = ' '.join(str(e or '') for _, e in _exprs(panel))
    if re.search(r'(\*\s*100\b|\b100\s*\*)', expr):
        return 'percent', 100
    if '/' in expr:
        return 'percentunit', 1
    return None


def _slots(layout):
    """(section name, row index, x, slot) in layout order; every row must fill the grid width exactly."""
    if layout.get('panel_height') != 8 or len(layout.get('sections', [])) != 5:
        raise ValueError('Expected five sections with panel height 8')
    out, row_index = [], 0
    for section in layout['sections']:
        for row in section['rows']:
            if any(not isinstance(slot.get('width'), int) or slot['width'] <= 0 for slot in row) or \
                    sum(slot['width'] for slot in row) != GRID_WIDTH:
                raise ValueError(f'layout row {row_index + 1} does not fill {GRID_WIDTH} columns')
            x = 0
            for slot in row:
                out.append((section['name'], row_index, x, slot))
                x += slot['width']
            row_index += 1
    if row_index != 10 or len(out) != 21:
        raise ValueError('Expected exactly ten rows and 21 chart slots')
    keys = [slot['match'].get('managed') or slot['match'].get('infra') for _, _, _, slot in out]
    if len(set(keys)) != len(keys):
        raise ValueError('Duplicate layout match key')
    return out


def layout_dashboard(document, layout, panels):
    """Re-arrange an already managed 21-panel dashboard; refuse anything unexpected. Input is not modified."""
    result = copy.deepcopy(document)
    dashboard = _dashboard(result)
    existing = dashboard.get('panels')
    if not isinstance(existing, list):
        raise ValueError('Dashboard panels are missing')
    if any(p.get('type') == 'row' or p.get('panels') for p in existing):
        raise ValueError('Row panels or nested panels are not expected; review the dashboard manually')
    slots = _slots(layout)
    if len(existing) != len(slots) or len(panels) + len(INFRA_ROLES) != len(slots):
        raise ValueError(f'Expected exactly {len(slots)} panels (17 managed + 4 infrastructure), '
                         f'found {len(existing)}; use --mode append for the 4-panel dashboard')
    ids = [p.get('id') for p in existing]
    if any(not isinstance(i, int) or isinstance(i, bool) or i <= 0 for i in ids) or len(set(ids)) != len(ids):
        raise ValueError('Panel ids must be unique positive integers')
    v1 = {p['title']: p for p in panels}
    managed_title = {}                                   # current title (v1 or v2) -> v1 title
    infra_title = {}                                     # v2 infrastructure title -> role
    for _, _, _, slot in slots:
        if 'managed' in slot['match']:
            managed_title[slot['match']['managed']] = managed_title[slot['title']] = slot['match']['managed']
        else:
            infra_title[slot['title']] = slot['match']['infra']
    found = {}
    for panel in existing:
        if MARKER in str(panel.get('description', '')):
            key = managed_title.get(panel.get('title'))
            if key is None:
                raise ValueError(f'Unknown managed panel {panel.get("title")!r}')
            if _exprs(panel) != _exprs(v1[key]):
                raise ValueError(f'PromQL of {panel.get("title")!r} differs from panels.json; review it manually')
        else:
            key = _infra_role(panel, infra_title)
            if key is None:
                raise ValueError(f'Cannot identify infrastructure panel {panel.get("title")!r}')
        if key in found:
            raise ValueError(f'Two panels match {key!r}; review the dashboard manually')
        found[key] = panel
    by_key = {slot['match'].get('managed') or slot['match']['infra']: (section, row, x, slot)
              for section, row, x, slot in slots}
    if set(found) != set(by_key):
        raise ValueError(f'Missing panels: {sorted(set(by_key) - set(found))}')
    height = layout['panel_height']
    for key, panel in found.items():
        section, row, x, slot = by_key[key]
        defaults = panel.setdefault('fieldConfig', {}).setdefault('defaults', {})
        panel['title'] = slot['title']
        text = f'{section}. {slot["description"]}'
        panel['description'] = f'{MARKER} {text}' if 'managed' in slot['match'] else text
        if slot.get('percent'):
            scale = _percent_scale(panel)
            if scale is None:
                raise ValueError(f'Cannot determine percent scale for {slot["title"]!r}')
            defaults.update(unit=scale[0], min=0, max=scale[1])
        for field in ('unit', 'min', 'max', 'decimals'):
            if field in slot:
                defaults[field] = slot[field]
        if slot.get('mappings') == 'up_down':
            defaults['mappings'] = copy.deepcopy(UP_DOWN)
        for target in panel.get('targets') or []:
            if target.get('refId') in slot.get('legends', {}):
                target['legendFormat'] = slot['legends'][target['refId']]
        if 'infra' in slot['match']:
            panel['targets'][0]['legendFormat'] = INFRA_LEGENDS[slot['match']['infra']]
        panel['gridPos'] = {'h': height, 'w': slot['width'], 'x': x, 'y': row * height}
    existing.sort(key=lambda p: (p['gridPos']['y'], p['gridPos']['x']))
    validate_layout(result, layout)
    return result


def validate_layout(document, layout) -> list[dict]:
    """Raise on duplicate ids, overlaps, panels outside the grid or a layout mismatch; return rows of the plan."""
    panels = _dashboard(document)['panels']
    slots = _slots(layout)
    if len(panels) != len(slots) or len({p['id'] for p in panels}) != len(panels):
        raise ValueError('Expected unique panel ids for every layout slot')
    cells = set()
    for p in panels:
        g = p['gridPos']
        if g['x'] < 0 or g['x'] + g['w'] > GRID_WIDTH:
            raise ValueError(f'Panel {p["id"]} is outside the {GRID_WIDTH}-column grid')
        for cell in ((x, y) for x in range(g['x'], g['x'] + g['w']) for y in range(g['y'], g['y'] + g['h'])):
            if cell in cells:
                raise ValueError(f'Panel {p["id"]} overlaps another panel')
            cells.add(cell)
    plan = [{'section': section, 'row': row + 1, 'title': slot['title'], 'width': slot['width']}
            for section, row, _, slot in slots]
    for panel, (_, row, x, slot) in zip(panels, slots):
        if panel.get('title') != slot['title']:
            raise ValueError('Panel order does not follow the layout')
        expected = {'x': x, 'y': row * layout['panel_height'],
                    'w': slot['width'], 'h': layout['panel_height']}
        if any(panel['gridPos'].get(axis) != value for axis, value in expected.items()):
            raise ValueError(f'Panel {panel["id"]} does not match its declared grid position')
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--mode', choices=('append', 'layout'), default='append')
    parser.add_argument('--input', type=Path, required=True, help='a COPY of the provisioned dashboard JSON')
    parser.add_argument('--output', type=Path, required=True, help='a new candidate file (never overwritten)')
    parser.add_argument('--datasource-name', help='append mode: the existing Prometheus datasource')
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error('--output must be a separate candidate file')
    panels = json.loads((ROOT / 'deploy/observability/panels.json').read_text())
    document = json.loads(args.input.read_text())
    if args.mode == 'append':
        if not args.datasource_name:
            parser.error('--datasource-name is required in append mode')
        result = merge_dashboard(document, panels, args.datasource_name)
    else:
        layout = json.loads((ROOT / 'deploy/observability/layout.json').read_text())
        result = layout_dashboard(document, layout, panels)
        for p in _dashboard(result)['panels']:
            g = p['gridPos']
            print(f"id {p['id']:>3}  y={g['y']:>2} x={g['x']:>2} w={g['w']:>2}  {p['title']}")
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(f'Prepared local dashboard candidate {args.output} ({args.mode}). Nothing uploaded.')


if __name__ == '__main__':
    main()
