"""Validate the static publication without accessing any account or market source."""
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ASSETS = {'cni_growth', 'cni_value', 'nasdaq', 'china_bond_composite', 'gold'}
FORBIDDEN = ('/Users/', '/private/', 'tzzb.10jqka.com.cn', 'Ii8kkCY', 'Bearer ',
             'ghp_', 'gho_', 'github_pat_', 'PRIVATE KEY', 'runner_token',
             'dispatch_token', 'client_secret', 'run_manifest_path')


def validate(snapshot, calendar, now=None):
    now = now or datetime.now(timezone.utc)
    encoded = json.dumps(snapshot, ensure_ascii=False, allow_nan=False)
    if any(value in encoded for value in FORBIDDEN):
        raise ValueError('private metadata in snapshot')
    if snapshot['schema_version'] != 'portfolio.monitor_snapshot.v3':
        raise ValueError('unsupported schema')
    authority = snapshot['authority']
    if (authority['status'], authority['framework'], authority['framework_version'], authority['runtime']) != (
        'passed', 'NautilusTrader', '1.230.0', 'BacktestNode+ParquetDataCatalog'
    ) or not authority.get('run_id'):
        raise ValueError('authority failed')
    freshness = snapshot['freshness']
    if freshness['data_end'] != freshness['required_session']:
        raise ValueError('snapshot did not pass original freshness gate')
    account = snapshot['account']
    if account['confirmation_status'] != 'unconfirmed' or account['account_name'] != '华宝':
        raise ValueError('unconfirmed Huabao monitor observation required')
    if any(account.get(key) is not None for key in ('plan_id', 'plan_status', 'account_action', 'net_trade_amount')):
        raise ValueError('account plan must not be published')
    rows = account['rows']
    if len(rows) != 5 or {row['asset'] for row in rows} != ASSETS:
        raise ValueError('complete five-asset display required')
    for row in rows:
        if any(row.get(key) is not None for key in ('action', 'trade_amount', 'plan_target_amount')):
            raise ValueError('trade plan in monitor row')
    amounts = [float(row['actual_amount']) for row in rows] + [float(account['cash_amount']), float(account['non_strategy_amount'])]
    total = float(account['total_value'])
    if not math.isfinite(total) or total <= 0 or any(not math.isfinite(x) or x < 0 for x in amounts) or abs(sum(amounts)-total) > .02:
        raise ValueError('inconsistent holdings')
    if set(snapshot['performance']['assets']) != ASSETS:
        raise ValueError('missing overlay asset')
    for key, horizon in snapshot['performance']['horizons'].items():
        if horizon['end_date'] != freshness['data_end'] or len(horizon['points']) < 2:
            raise ValueError('inconsistent model chart dates')
        for asset in snapshot['performance']['assets'].values():
            if [p['date'] for p in asset['horizons'][key]['points']] != [p['date'] for p in horizon['points']]:
                raise ValueError('asset overlay dates do not match model')
    publication = snapshot['publication']
    if publication['mode'] not in ('daily', 'migration'):
        raise ValueError('unknown publication mode')
    if publication['mode'] == 'migration':
        if publication.get('source_commit') != '1b5f485c3aadf3ee551145dcb4d9999012a2792b':
            raise ValueError('migration must identify the inspected live source')
    else:
        closes = [item for item in calendar['closes'] if datetime.fromisoformat(item['close']) <= now]
        if not closes or now.date().isoformat() > calendar['valid_until']:
            raise ValueError('calendar unavailable')
        required = closes[-1]['date']
        age = (now - datetime.fromisoformat(account['observed_at'])).total_seconds()
        if freshness['data_end'] != required or account['valuation_date'] != required or not 0 <= age <= 86400:
            raise ValueError('daily snapshot is stale')
    return snapshot


def main():
    site = Path(__file__).resolve().parent / 'site'
    expected = {'index.html', 'snapshot.json', 'calendar.json', 'freshness.js', '.nojekyll'}
    if {p.name for p in site.iterdir()} != expected or any(p.is_symlink() for p in site.iterdir()):
        raise ValueError('unexpected public file')
    for path in site.iterdir():
        if path.stat().st_size > 5_000_000:
            raise ValueError('unexpected publication size')
        if any(value in path.read_text() for value in FORBIDDEN):
            raise ValueError('private content in publication')
    html = (site / 'index.html').read_text()
    if '/api/' in html or 'chatgpt.site' in html:
        raise ValueError('old backend dependency')
    snapshot = validate(json.loads((site / 'snapshot.json').read_text()), json.loads((site / 'calendar.json').read_text()))
    print(json.dumps({'status':'passed', 'mode':snapshot['publication']['mode'], 'data_end':snapshot['freshness']['data_end']}))


if __name__ == '__main__':
    main()
