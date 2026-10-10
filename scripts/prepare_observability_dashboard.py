"""Append managed panels to an owner-exported dashboard. Offline; no Grafana API or overwrite."""
import argparse
import copy
import json
from pathlib import Path

MARKER = '[jobfit-observability-v1]'


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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--datasource-name', required=True)
    args = parser.parse_args()
    panels = Path(__file__).resolve().parents[1] / 'deploy/observability/panels.json'
    result = merge_dashboard(json.loads(args.input.read_text()), json.loads(panels.read_text()), args.datasource_name)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print('Prepared local dashboard artifact. Nothing uploaded.')


if __name__ == '__main__':
    main()
