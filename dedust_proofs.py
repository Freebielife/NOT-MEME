"""Read executed DeDust swap amounts from pool logs, excluding gas refunds."""
from functools import lru_cache
from assets import fetch, MASTER_RAW, token_amount, native_amount
from badges import raw_friendly

@lru_cache(maxsize=512)
def trace_for(tx):
    return fetch('/traces/' + tx)

def pool_amounts(trace, pool, wallet, kind, token, base_transactions=None):
    pool_raw = raw_friendly(pool)
    matches = []
    def walk(node):
        tx = node.get('transaction', {})
        if (tx.get('account', {}).get('address') == pool_raw
                and tx.get('success') is True and not tx.get('aborted')
                and (base_transactions is None or tx.get('hash') in base_transactions)):
            for msg in tx.get('out_msgs', []):
                if msg.get('decoded_op_name') != 'dedust_swap':
                    continue
                b = msg.get('decoded_body') or {}
                def asset(a):
                    if a.get('sum_type') == 'Native': return 'TON'
                    if a.get('sum_type') == 'Jetton':
                        j = a['jetton'];return str(j['workchain_id']) + ':' + j['address']
                    return None
                source, target = asset(b.get('asset_in', {})), asset(b.get('asset_out', {}))
                sender = (b.get('field4') or {}).get('sender_addr')
                if sender != wallet: continue
                if kind == 'sell' and source == MASTER_RAW and target == 'TON':
                    qty, ton = token_amount(b['amount_in']), native_amount(b['amount_out'])
                elif kind == 'buy' and source == 'TON' and target == MASTER_RAW:
                    qty, ton = token_amount(b['amount_out']), native_amount(b['amount_in'])
                else: continue
                if float(qty) > 0 and float(ton) > 0:
                    matches.append({'ton':ton, 'poolTokenAmount':qty, 'poolTx':tx['hash'], 'amountSource':'dedust_pool_log'})
        for child in node.get('children', []):walk(child)
    walk(trace)
    if len(matches) != 1:
        raise ValueError('Expected exactly one matching successful DeDust pool log')
    return matches[0]
