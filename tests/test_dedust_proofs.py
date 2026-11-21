import copy
import unittest
from assets import MASTER_RAW
from trades import PRIMARY
from badges import raw_friendly
from dedust_proofs import pool_amounts

WALLET='0:'+'5'*64
HASH='1'*64
class DeDustProofTests(unittest.TestCase):
    def trace(self):
        jetton={'sum_type':'Jetton','jetton':{'workchain_id':0,'address':MASTER_RAW.split(':')[1]}}
        body={'asset_in':jetton,'asset_out':{'sum_type':'Native'},'amount_in':'2000000000','amount_out':'112375','field4':{'sender_addr':WALLET}}
        return {'transaction':{'account':{'address':raw_friendly(PRIMARY)},'hash':HASH,'success':True,'aborted':False,'out_msgs':[{'decoded_op_name':'dedust_swap','decoded_body':body}]}}
    def test_sale_uses_pool_output_not_wallet_gas_refund(self):
        # Real failure: indexer called a 0.274111927 gas refund the proceeds
        # of a two-token sale. Executed pool log says 0.000112375 TON.
        p=pool_amounts(self.trace(),PRIMARY,WALLET,'sell','2',[HASH])
        self.assertEqual(p['ton'],'0.000112375')
        self.assertEqual(p['amountSource'],'dedust_pool_log')
        self.assertEqual(p['poolTokenAmount'],'2')
    def test_wrong_wallet_failed_tx_and_unrelated_action_are_rejected(self):
        for field,value in [('success',False),('aborted',True),('hash','2'*64)]:
            t=self.trace();t['transaction'][field]=value
            with self.assertRaises(ValueError):pool_amounts(t,PRIMARY,WALLET,'sell','2',[HASH])
        with self.assertRaises(ValueError):pool_amounts(self.trace(),PRIMARY,'0:'+'6'*64,'sell','2',[HASH])
    def test_buy_uses_native_input_and_token_output(self):
        t=self.trace();b=t['transaction']['out_msgs'][0]['decoded_body'];b['asset_in'],b['asset_out']=b['asset_out'],b['asset_in'];b['amount_in']='112375';b['amount_out']='2000000000'
        self.assertEqual(pool_amounts(t,PRIMARY,WALLET,'buy','2',[HASH])['ton'],'0.000112375')
    def test_ambiguous_logs_are_not_guessed(self):
        t=self.trace();t['transaction']['out_msgs']*=2
        with self.assertRaises(ValueError):pool_amounts(t,PRIMARY,WALLET,'sell','2',[HASH])
