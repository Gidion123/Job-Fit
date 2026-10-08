"""Read-only catalog fingerprint of the application schema (CP3 Alembic baseline, D-098).

The fingerprint describes every object in the ``public`` schema that the application could
depend on: tables and other relations, columns (type, nullability, default, generated
expression, identity, collation), constraints, indexes, triggers, functions, user types and the
installed extensions. Extension-owned objects are left out (they belong to the extension).

Alembic's own bookkeeping table is not application schema. It is left out only when it has
exactly Alembic's structure; any other table of that name, or any other unexpected object,
stays in the fingerprint and makes a comparison fail. Its content is reported separately by
``revision_state``.

Nothing here writes: callers open the connection read-only, and no row data is read except the
Alembic revision string.
"""
from __future__ import annotations

from jobfit.db.migrate import ALEMBIC_VERSION_TABLE

SCHEMA = 'public'
# The structure Alembic creates for its version table (alembic.runtime.migration).
_ALEMBIC_COLUMNS = [['version_num', 'character varying(32)', True, None, '', '', None]]
_ALEMBIC_CONSTRAINTS = [['alembic_version_pkc', 'p', 'PRIMARY KEY (version_num)']]
_ALEMBIC_INDEXES = [['alembic_version_pkc',
                     'CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num)']]

_NOT_EXTENSION_OWNED = (
    "NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.classid = {cls}::regclass "
    "AND d.objid = {oid} AND d.deptype = 'e')")


def _rows(conn, sql, params=None):
    return [list(r) for r in conn.execute(sql, params or {}).fetchall()]


def _relations(conn):
    return {name: kind for name, kind in _rows(conn, (
        "SELECT c.relname, c.relkind::text FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE n.nspname = %(schema)s AND c.relkind IN ('r', 'p', 'v', 'm', 'f', 'S', 'c') AND "
        + _NOT_EXTENSION_OWNED.format(cls="'pg_class'", oid='c.oid')), {'schema': SCHEMA})}


def _columns(conn, table):
    # Relative order of the live (not dropped) columns, so a drop-and-re-add cycle compares equal.
    return _rows(conn, (
        "SELECT a.attname, format_type(a.atttypid, a.atttypmod), a.attnotnull, "
        "pg_get_expr(ad.adbin, ad.adrelid), a.attgenerated::text, a.attidentity::text, "
        "CASE WHEN a.attcollation <> t.typcollation THEN co.collname END "
        "FROM pg_attribute a JOIN pg_type t ON t.oid = a.atttypid "
        "LEFT JOIN pg_attrdef ad ON ad.adrelid = a.attrelid AND ad.adnum = a.attnum "
        "LEFT JOIN pg_collation co ON co.oid = a.attcollation "
        "WHERE a.attrelid = %(rel)s::regclass AND a.attnum > 0 AND NOT a.attisdropped ORDER BY a.attnum"),
        {'rel': f'{SCHEMA}.{table}'})


def _constraints(conn, table):
    return _rows(conn, (
        "SELECT conname, contype::text, pg_get_constraintdef(oid, true) FROM pg_constraint "
        "WHERE conrelid = %(rel)s::regclass ORDER BY conname"), {'rel': f'{SCHEMA}.{table}'})


def _indexes(conn, table):
    return _rows(conn, (
        "SELECT i.relname, pg_get_indexdef(x.indexrelid) FROM pg_index x JOIN pg_class i ON i.oid = x.indexrelid "
        "WHERE x.indrelid = %(rel)s::regclass ORDER BY i.relname"), {'rel': f'{SCHEMA}.{table}'})


def _alembic_table_is_standard(conn) -> bool:
    return (_columns(conn, ALEMBIC_VERSION_TABLE) == _ALEMBIC_COLUMNS
            and _constraints(conn, ALEMBIC_VERSION_TABLE) == _ALEMBIC_CONSTRAINTS
            and _indexes(conn, ALEMBIC_VERSION_TABLE) == _ALEMBIC_INDEXES
            and not _rows(conn, "SELECT 1 FROM pg_trigger WHERE tgrelid = %(rel)s::regclass",
                          {'rel': f'{SCHEMA}.{ALEMBIC_VERSION_TABLE}'}))


def fingerprint(conn) -> dict:
    """Application schema of ``public``: ``objects`` (compared) and ``environment`` (reported)."""
    relations = _relations(conn)
    if relations.get(ALEMBIC_VERSION_TABLE) == 'r' and _alembic_table_is_standard(conn):
        del relations[ALEMBIC_VERSION_TABLE]
    tables = {}
    for name, kind in sorted(relations.items()):
        entry = {'kind': kind}
        if kind in ('r', 'p', 'v', 'm', 'f'):
            entry['columns'] = _columns(conn, name)
        if kind in ('r', 'p', 'f'):
            entry['constraints'] = _constraints(conn, name)
        if kind in ('r', 'p', 'm'):
            entry['indexes'] = _indexes(conn, name)
        tables[name] = entry
    triggers = _rows(conn, (
        "SELECT c.relname, t.tgname, pg_get_triggerdef(t.oid) FROM pg_trigger t "
        "JOIN pg_class c ON c.oid = t.tgrelid JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE n.nspname = %(schema)s AND NOT t.tgisinternal ORDER BY c.relname, t.tgname"), {'schema': SCHEMA})
    functions = _rows(conn, (
        "SELECT p.proname, p.prokind::text, CASE WHEN p.prokind IN ('f', 'p') THEN pg_get_functiondef(p.oid) END "
        "FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE n.nspname = %(schema)s AND "
        + _NOT_EXTENSION_OWNED.format(cls="'pg_proc'", oid='p.oid') + " ORDER BY p.proname, 3"), {'schema': SCHEMA})
    types = _rows(conn, (
        "SELECT t.typname, t.typtype::text FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace "
        "WHERE n.nspname = %(schema)s AND t.typtype IN ('d', 'e', 'r', 'm') AND "
        + _NOT_EXTENSION_OWNED.format(cls="'pg_type'", oid='t.oid') + " ORDER BY t.typname"), {'schema': SCHEMA})
    extensions = _rows(conn, "SELECT e.extname, n.nspname, e.extversion FROM pg_extension e "
                             "JOIN pg_namespace n ON n.oid = e.extnamespace ORDER BY e.extname")
    server = conn.execute('SHOW server_version_num').fetchone()[0]
    return {'objects': {'tables': tables, 'triggers': triggers, 'functions': functions, 'types': types,
                        'extensions': [[name, schema] for name, schema, _ in extensions]},
            'environment': {'server_version_num': int(server),
                            'extension_versions': {name: version for name, _, version in extensions}}}


def revision_state(conn) -> str:
    """'absent', 'empty', 'malformed' or the single Alembic revision string."""
    if _relations(conn).get(ALEMBIC_VERSION_TABLE) is None:
        return 'absent'
    if not _alembic_table_is_standard(conn):
        return 'malformed'
    rows = _rows(conn, f'SELECT version_num FROM {SCHEMA}.{ALEMBIC_VERSION_TABLE}')
    if not rows:
        return 'empty'
    return rows[0][0] if len(rows) == 1 else 'malformed'


def compare(expected: dict, actual: dict) -> list[str]:
    """Structural differences of the ``objects`` part, without any row data. Empty means equal."""
    differences = []

    def walk(path, a, b):
        if isinstance(a, dict) and isinstance(b, dict):
            for key in sorted(set(a) | set(b)):
                if key not in b:
                    differences.append(f'{path}/{key}: missing')
                elif key not in a:
                    differences.append(f'{path}/{key}: unexpected')
                else:
                    walk(f'{path}/{key}', a[key], b[key])
        elif a != b:
            differences.append(f'{path}: expected {a!r}, found {b!r}')

    walk('', expected['objects'], actual['objects'])
    return differences
