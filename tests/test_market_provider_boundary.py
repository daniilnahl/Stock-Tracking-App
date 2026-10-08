"""Bounded static provider-boundary enforcement with controlled violations.

This detects ordinary literal fields/imports/calls, not dynamic obfuscation or
every possible HTTP library. Runtime/domain guards complement this regression.
"""

import ast
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
HTTP_ROOTS = {'urllib', 'http', 'requests', 'urllib3', 'httpx', 'aiohttp', 'socket', 'ssl', 'certifi'}
SCHEMA_KEYS = {'symbol', 'price', 'companyName', 'marketCap', 'mktCap', 'timestamp',
               '1D', '5D', '1M', '3M', '6M', '1Y', '3Y', '5Y'}
LEGACY_IMPORTS = {'urllib.request.urlopen', 'urllib.error.HTTPError', 'urllib.error.URLError', 'certifi'}


def boundary_findings(source, path):
    tree = ast.parse(source)
    adapter = path.startswith('src/stock_tracker/providers/')
    # ADR-0010's neutral sidecar has a required symbol field. This one mapping
    # is persistence data, not an FMP response parser; all HTTP, concrete-adapter
    # and other provider-payload checks continue to apply to this module.
    neutral_history = path == 'src/stock_tracker/persistence/history_cache.py'
    legacy = path == 'utils/utility_module.py'
    aliases = {}
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports = [(item.asname or item.name.split('.')[0], item.name) for item in node.names]
        elif isinstance(node, ast.ImportFrom):
            imports = [(item.asname or item.name, (node.module or '') + '.' + item.name) for item in node.names]
        else:
            continue
        for alias, module in imports:
            aliases[alias] = module
            if not adapter and module.split('.')[0] in HTTP_ROOTS and not (legacy and module in LEGACY_IMPORTS):
                findings.append('direct HTTP import')
            if not adapter and (module.startswith('stock_tracker.providers.fmp')
                                or module.startswith('stock_tracker.providers.transport')):
                findings.append('caller imports concrete provider or HTTP boundary')

    def qualified(node):
        if isinstance(node, ast.Name):
            return aliases.get(node.id, node.id)
        if isinstance(node, ast.Attribute):
            return qualified(node.value) + '.' + node.attr
        return ''

    def visit(node, function=None):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            function = node.name
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if not adapter and 'financialmodelingprep.com' in node.value.lower():
                findings.append('FMP URL outside adapter')
        if not adapter:
            key = node.slice if isinstance(node, ast.Subscript) else None
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'get' and node.args:
                key = node.args[0]
            if (isinstance(key, ast.Constant) and key.value in SCHEMA_KEYS
                    and not (neutral_history and key.value == 'symbol')):
                findings.append('provider payload field outside adapter')
        if isinstance(node, ast.Call):
            name = qualified(node.func)
            if name.split('.')[-1] == 'get_jsonparsed_data':
                findings.append('maintained caller uses retained legacy helper')
            network = name.split('.')[0] in HTTP_ROOTS or name.split('.')[-1] in {'urlopen', 'build_opener'}
            if network and not adapter and not (legacy and function == 'get_jsonparsed_data'
                                               and name in {'urllib.request.urlopen', 'certifi.where'}):
                findings.append('direct HTTP call')
        for child in ast.iter_child_nodes(node):
            visit(child, function)
    visit(tree)
    return findings


def test_runtime_sources_enforce_market_provider_boundary():
    sources = list(ROOT.glob('*.py')) + list((ROOT / 'utils').glob('*.py')) + list((ROOT / 'src').rglob('*.py'))
    findings = {str(path.relative_to(ROOT)): boundary_findings(path.read_text(encoding='utf-8-sig'), path.relative_to(ROOT).as_posix())
                for path in sources}
    assert not {path: failures for path, failures in findings.items() if failures}


@pytest.mark.parametrize('source', [
    'url = "https://financialmodelingprep.com/stable/quote"',
    'price = payload[0]["price"]', 'cap = payload.get("marketCap")',
    'from urllib.request import urlopen as fetch\nfetch(url)',
    'import requests as client\nclient.get(url)',
    'from utils.utility_module import get_jsonparsed_data as fetch\nfetch(url)',
    'from utils import utility_module as um\num.get_jsonparsed_data(url)',
    'import utils.utility_module as um\num.get_jsonparsed_data(url)',
    'from stock_tracker.providers.fmp import FMPMarketDataProvider',
    'from stock_tracker.providers import transport',
])
def test_controlled_application_violations_are_rejected(source):
    assert boundary_findings(source, 'stock.py')


def test_generic_utility_exemption_does_not_allow_new_http_or_schema_callers():
    retained = 'from urllib.request import urlopen\ndef get_jsonparsed_data(url):\n    return urlopen(url)\n'
    assert boundary_findings(retained, 'utils/utility_module.py') == []
    assert boundary_findings(retained + '\ndef check_ticker(symbol, key):\n    return urlopen(symbol)\n', 'utils/utility_module.py')
    assert boundary_findings(retained + '\ndef check_ticker(symbol, key):\n    return get_jsonparsed_data(symbol)\n', 'utils/utility_module.py')
    assert boundary_findings(retained + '\ndef helper(data):\n    return data["mktCap"]\n', 'utils/utility_module.py')
    assert boundary_findings(retained + '\nurl = "https://financialmodelingprep.com/stable/quote"', 'utils/utility_module.py')


def test_accepted_neutral_cache_symbol_mapping_keeps_provider_boundary_guards():
    path = 'src/stock_tracker/persistence/history_cache.py'
    assert boundary_findings('symbol = key["symbol"]', path) == []
    for source in ('price = payload["price"]', 'cap = payload["marketCap"]',
                   'from urllib.request import urlopen',
                   'from stock_tracker.providers.fmp import FMPMarketDataProvider',
                   'url = "https://financialmodelingprep.com/stable/quote"'):
        assert boundary_findings(source, path)
    assert boundary_findings('symbol = payload["symbol"]', 'stock.py')
