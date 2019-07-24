from behave import given, when, then
import base64
from algosdk import kmd
from algosdk import transaction
from algosdk import encoding
from algosdk import algod
from algosdk import account
from algosdk import mnemonic
from algosdk import wallet
from os.path import expanduser
import os.path


@when("I create a wallet")
def create_wallet(context):
    context.wallet_name = "Walletpy"
    context.wallet_pswd = ""
    context.wallet_id = context.kcl.create_wallet(context.wallet_name, context.wallet_pswd)["id"]


@then("the wallet should exist")
def wallet_exist(context):
    wallets = context.kcl.list_wallets()
    wallet_names = [w["name"] for w in wallets]
    assert context.wallet_name in wallet_names


@when("I get the wallet handle")
def get_handle(context):
    context.handle = context.kcl.init_wallet_handle(context.wallet_id, context.wallet_pswd)


@then("I can get the master derivation key")
def get_mdk(context):
    mdk = context.kcl.export_master_derivation_key(context.handle, context.wallet_pswd)
    assert mdk


@when("I rename the wallet")
def rename_wallet(context):
    context.wallet_name = "Walletpy_new"
    context.kcl.rename_wallet(context.wallet_id, context.wallet_pswd, context.wallet_name)


@then("I can still get the wallet information with the same handle")
def get_wallet_info(context):
    info = context.kcl.get_wallet(context.handle)
    assert info


@when("I renew the wallet handle")
def renew_handle(context):
    context.kcl.renew_wallet_handle(context.handle)


@when("I release the wallet handle")
def release_handle(context):
    context.kcl.release_wallet_handle(context.handle)


@then("the wallet handle should not work")
def try_handle(context):
    try:
        context.renew_wallet_handle(context.handle)
        context.error = False
    except:
        context.error = True
    assert context.error


@given('payment transaction parameters {fee} {fv} {lv} "{gh}" "{to}" "{close}" {amt} "{gen}" "{note}"')
def txn_params(context, fee, fv, lv, gh, to, close, amt, gen, note):
    context.fee = int(fee)
    context.fv = int(fv)
    context.lv = int(lv)
    context.gh = gh
    context.to = to
    context.amt = int(amt)
    if close == "none":
        context.close = None
    else:
        context.close = close
    if note == "none":
        context.note = None
    else:
        context.note = base64.b64decode(note)
    if gen == "none":
        context.gen = None
    else:
        context.gen = gen


@given('mnemonic for private key "{mn}"')
def mn_for_sk(context, mn):
    context.sk = mnemonic.to_private_key(mn)
    context.pk = account.address_from_private_key(context.sk)


@when('I create the payment transaction')
def create_paytxn(context):
    context.txn = transaction.PaymentTxn(context.pk, context.fee, context.fv, context.lv, context.gh, context.to, context.amt, context.close, context.note, context.gen)
    context.old_enc = encoding.msgpack_encode(context.txn)
    context.dec = context.txn


@given('multisig addresses "{addresses}"')
def msig_addresses(context, addresses):
    addresses = addresses.split(" ")
    context.msig = transaction.Multisig(1, 2, addresses)


@when("I create the multisig payment transaction")
def create_msigpaytxn(context):
    context.txn = transaction.PaymentTxn(context.msig.address(), context.fee, context.fv, context.lv, context.gh, context.to, context.amt, context.close, context.note, context.gen)
    context.mtx = transaction.MultisigTransaction(context.txn, context.msig)
    context.dec = context.mtx


@when("I sign the multisig transaction with the private key")
def sign_msig(context):
    context.mtx.sign(context.sk)


@when("I sign the transaction with the private key")
def sign_with_sk(context):
    context.stx = context.txn.sign(context.sk)


@then('the signed transaction should equal the golden "{golden}"')
def equal_golden(context, golden):
    assert encoding.msgpack_encode(context.stx) == golden


@then('the multisig address should equal the golden "{golden}"')
def equal_msigaddr_golden(context, golden):
    assert context.msig.address() == golden


@then('the multisig transaction should equal the golden "{golden}"')
def equal_msig_golden(context, golden):
    assert encoding.msgpack_encode(context.mtx) == golden


@when("I get versions with algod")
def acl_v(context):
    context.versions = context.acl.versions()["versions"]


@then("v1 should be in the versions")
def v1_in_versions(context):
    assert "v1" in context.versions


@when("I get versions with kmd")
def kcl_v(context):
    context.versions = context.kcl.versions()


@when("I get the status")
def status(context):
    context.status = context.acl.status()


@when("I get status after this block")
def status_block(context):
    context.status_after = context.acl.status_after_block(context.status["lastRound"])


@then("the rounds should be equal")
def rounds_eq(context):
    assert context.status["lastRound"] < context.status_after["lastRound"]


@then("I can get the block info")
def block(context):
    context.block = context.acl.block_info(context.status["lastRound"]+1)


@when("I import the multisig")
def import_msig(context):
    context.wallet.import_multisig(context.msig)


@then("the multisig should be in the wallet")
def msig_in_wallet(context):
    msigs = context.wallet.list_multisig()
    assert context.msig.address() in msigs


@when("I export the multisig")
def exp_msig(context):
    context.exp = context.wallet.export_multisig(context.msig.address())


@then("the multisig should equal the exported multisig")
def msig_eq(context):
    assert encoding.msgpack_encode(context.msig) == encoding.msgpack_encode(context.exp)


@when("I delete the multisig")
def delete_msig(context):
    context.wallet.delete_multisig(context.msig.address())


@then("the multisig should not be in the wallet")
def msig_not_in_wallet(context):
    msigs = context.wallet.list_multisig()
    assert context.msig.address() not in msigs


@when("I generate a key using kmd")
def gen_key_kmd(context):
    context.pk = context.wallet.generate_key()


@then("the key should be in the wallet")
def key_in_wallet(context):
    keys = context.wallet.list_keys()
    assert context.pk in keys


@when("I delete the key")
def delete_key(context):
    context.wallet.delete_key(context.pk)


@then("the key should not be in the wallet")
def key_not_in_wallet(context):
    keys = context.wallet.list_keys()
    assert context.pk not in keys


@when("I generate a key")
def gen_key(context):
    context.sk, context.pk = account.generate_account()


@when("I import the key")
def import_key(context):
    context.wallet.import_key(context.sk)


@then("the private key should be equal to the exported private key")
def sk_eq_export(context):
    exp = context.wallet.export_key(context.pk)
    assert context.sk == exp
    context.wallet.delete_key(context.pk)


@given("a kmd client")
def kmd_client(context):
    home = expanduser("~")
    data_dir_path = home + "/node/network/Node/"
    kmd_folder_name = "kmd-v0.5/"
    kmd_token = open(data_dir_path + kmd_folder_name + "kmd.token",
                     "r").read().strip("\n")
    kmd_address = "http://" + open(data_dir_path + kmd_folder_name + "kmd.net",
                                   "r").read().strip("\n")
    context.kcl = kmd.KMDClient(kmd_token, kmd_address)


@given("an algod client")
def algod_client(context):
    home = expanduser("~")
    data_dir_path = home + "/node/network/Node/"
    algod_token = open(data_dir_path + "algod.token", "r").read().strip("\n")
    algod_address = "http://" + open(data_dir_path + "algod.net",
                                     "r").read().strip("\n")
    context.acl = algod.AlgodClient(algod_token, algod_address)


@given("wallet information")
def wallet_info(context):
    context.wallet_name = "unencrypted-default-wallet"
    context.wallet_pswd = ""
    context.wallet = wallet.Wallet(context.wallet_name, context.wallet_pswd, context.kcl)
    context.wallet_id = context.wallet.id
    context.accounts = context.wallet.list_keys()


@given('default transaction with parameters {amt} "{note}"')
def default_txn(context, amt, note):
    params = context.acl.suggested_params()
    context.last_round = params["lastRound"]
    if note == "none":
        note = None
    else:
        note = base64.b64decode(note)
    context.txn = transaction.PaymentTxn(context.accounts[0], params["fee"], context.last_round, context.last_round+1000, params["genesishashb64"], context.accounts[1], int(amt), note=note, gen=params["genesisID"])
    context.pk = context.accounts[0]


@given('default multisig transaction with parameters {amt} "{note}"')
def default_msig_txn(context, amt, note):
    params = context.acl.suggested_params()
    context.last_round = params["lastRound"]
    if note == "none":
        note = None
    else:
        note = base64.b64decode(note)
    context.msig = transaction.Multisig(1, 1, context.accounts)
    context.txn = transaction.PaymentTxn(context.msig.address(), params["fee"], context.last_round, context.last_round + 1000, params["genesishashb64"], context.accounts[1], int(amt), note=note, gen=params["genesisID"])
    context.mtx = transaction.MultisigTransaction(context.txn, context.msig)
    context.pk = context.accounts[0]


@when("I get the private key")
def get_sk(context):
    context.sk = context.wallet.export_key(context.pk)


@when("I send the transaction")
def send_txn(context):
    context.balance = context.acl.account_info(context.pk)["amountwithoutpendingrewards"]
    context.acl.send_raw_transaction(context.stx)


@when("I send the multisig transaction")
def send_msig_txn(context):
    try:
        context.acl.send_raw_transaction(context.mtx)
    except:
        context.error = True


@then("the transaction should go through")
def check_txn(context):
    context.acl.status_after_block(context.last_round+2)
    assert "type" in context.acl.transaction_info(context.pk, context.txn.get_txid())


@then("the transaction should not go through")
def txn_fail(context):
    assert context.error


@when("I sign the transaction with kmd")
def sign_kmd(context):
    context.stx_kmd = context.wallet.sign_transaction(context.txn)


@then("the signed transaction should equal the kmd signed transaction")
def sign_both_equal(context):
    assert encoding.msgpack_encode(context.stx) == encoding.msgpack_encode(context.stx_kmd)


@when("I sign the multisig transaction with kmd")
def sign_msig_kmd(context):
    context.mtx_kmd = context.wallet.sign_multisig_transaction(context.accounts[0], context.mtx)


@then("the multisig transaction should equal the kmd signed multisig transaction")
def sign_msig_both_equal(context):
    assert encoding.msgpack_encode(context.mtx) == encoding.msgpack_encode(context.mtx_kmd)


@when("I read a transaction from file")
def read_txn(context):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_path = os.path.dirname(os.path.dirname(dir_path))
    context.txn = transaction.retrieve_from_file(dir_path + "/raw.tx")[0]
    

@when("I write the transaction to file")
def write_txn(context):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_path = os.path.dirname(os.path.dirname(dir_path))
    transaction.write_to_file([context.txn], dir_path + "/raw.tx")


@then("the transaction should still be the same")
def check_enc(context):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_path = os.path.dirname(os.path.dirname(dir_path))

    new = transaction.retrieve_from_file(dir_path + "/raw.tx")
    old = transaction.retrieve_from_file(dir_path + "/old.tx")
    assert encoding.msgpack_encode(new[0]) == encoding.msgpack_encode(old[0])


@then("I do my part")
def check_save_txn(context):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_path = os.path.dirname(os.path.dirname(dir_path))
    print(dir_path)
    stx = transaction.retrieve_from_file(dir_path + "/txn.tx")[0]
    txid = stx.transaction.get_txid()
    context.acl.status_after_block(stx.transaction.first_valid_round + 2)
    assert context.acl.transaction_info(stx.transaction.sender, txid)
    