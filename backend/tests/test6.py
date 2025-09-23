import os
import json
import logging
from flask import Flask, request, jsonify, Response
from dotenv import load_dotenv
import requests
from eth_account import Account
from x402.clients.requests import x402_requests
import base64
import time

load_dotenv()

raw_keys = os.getenv("PRIVATE_KEYS")
if not raw_keys:
    raise ValueError("Missing PRIVATE_KEYS in .env")
pk = raw_keys.split(",")[0].strip()
if not pk.startswith("0x"):
    pk = "0x" + pk
PRIVATE_KEY = pk

account = Account.from_key(PRIVATE_KEY)
session = x402_requests(account)

print(f'account: {account.address}')

def pay():
    method = "GET"
    api_url = "https://www.x402.org/protected"
    paid_resp = session.request(method, api_url, json={} if method != "GET" else None)

    print(f"Response status code: {paid_resp.status_code}")
    print(paid_resp.text)
    try:
        print(paid_resp.json())
    except ValueError:
        print("Response content is not valid JSON")

if __name__ == "__main__":
    print("Starting payment process...")
    pay()
