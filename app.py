import asyncio
import time
import httpx
import json
from collections import defaultdict
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
from cachetools import TTLCache
from typing import Tuple
from proto import FreeFire_pb2, main_pb2, AccountPersonalShow_pb2
from google.protobuf import json_format, message
from google.protobuf.message import Message
from Crypto.Cipher import AES
import base64

# === Settings ===

MAIN_KEY = base64.b64decode('WWcmdGMlREV1aDYlWmNeOA==')
MAIN_IV = base64.b64decode('Nm95WkRyMjJFM3ljaGpNJQ==')
USERAGENT = "Dalvik/2.1.0 (Linux; U; Android 13; CPH2095 Build/RKQ1.211119.001)"

# =============================================
# 🌍 অ্যাকাউন্ট ক্রেডেনশিয়ালস
# =============================================

ACCOUNT_CREDENTIALS = {
    "BD": {"uid": "5372860087", "password": "shappno_create-by-shappno_S7kkYNMy"},
    "IND": {"uid": "4269013803", "password": "MG24_GAMER_XSBOS_BY_SPIDEERIO_GAMING_TE5NG"},
    "ME": {"uid": "4555614387", "password": "‏S7LZFLTWZ3J7-S1X_TEAM"},
    "SG": {"uid": "4269012488", "password": "MG24_GAMER_U27YB_BY_SPIDEERIO_GAMING_0PNCN"},
    "ID": {"uid": "4269012488", "password": "MG24_GAMER_U27YB_BY_SPIDEERIO_GAMING_0PNCN"},
    "TH": {"uid": "4269012488", "password": "MG24_GAMER_U27YB_BY_SPIDEERIO_GAMING_0PNCN"},
    "VN": {"uid": "4269012488", "password": "MG24_GAMER_U27YB_BY_SPIDEERIO_GAMING_0PNCN"},
    "PK": {"uid": "4269012488", "password": "MG24_GAMER_U27YB_BY_SPIDEERIO_GAMING_0PNCN"},
    "BR": {"uid": "4269012488", "password": "MG24_GAMER_U27YB_BY_SPIDEERIO_GAMING_0PNCN"},
    "US": {"uid": "4269012488", "password": "MG24_GAMER_U27YB_BY_SPIDEERIO_GAMING_0PNCN"},
    "EU": {"uid": "4269012488", "password": "MG24_GAMER_U27YB_BY_SPIDEERIO_GAMING_0PNCN"},
}

# =============================================
# 🌍 রিজন কনফিগ
# =============================================

REGION_CONFIG = {
    "BD": {"server_url": "https://loginbp.ggblueshark.com", "release_version": "OB54"},
    "IND": {"server_url": "https://loginbp.ggpolarbear.com", "release_version": "OB54"},
    "ME": {"server_url": "https://loginbp.ggblueshark.com", "release_version": "OB54"},
    "SG": {"server_url": "https://loginbp.ggblueshark.com", "release_version": "OB54"},
    "ID": {"server_url": "https://loginbp.ggblueshark.com", "release_version": "OB54"},
    "TH": {"server_url": "https://loginbp.ggblueshark.com", "release_version": "OB54"},
    "VN": {"server_url": "https://loginbp.ggblueshark.com", "release_version": "OB54"},
    "PK": {"server_url": "https://loginbp.ggblueshark.com", "release_version": "OB54"},
    "BR": {"server_url": "https://loginbp.ggpolarbear.com", "release_version": "OB54"},
    "US": {"server_url": "https://loginbp.ggpolarbear.com", "release_version": "OB54"},
    "EU": {"server_url": "https://loginbp.ggblueshark.com", "release_version": "OB54"},
}

# === Flask App Setup ===

app = Flask(__name__)
CORS(app)
cache = TTLCache(maxsize=100, ttl=300)
cached_tokens = defaultdict(dict)
uid_region_cache = {}

# === Helper Functions ===

def pad(text: bytes) -> bytes:
    padding_length = AES.block_size - (len(text) % AES.block_size)
    return text + bytes([padding_length] * padding_length)

def unpad(text: bytes) -> bytes:
    padding_length = text[-1]
    if padding_length < 1 or padding_length > AES.block_size:
        return text
    return text[:-padding_length]

def aes_cbc_encrypt(key: bytes, iv: bytes, plaintext: bytes) -> bytes:
    aes = AES.new(key, AES.MODE_CBC, iv)
    return aes.encrypt(pad(plaintext))

def aes_cbc_decrypt(key: bytes, iv: bytes, ciphertext: bytes) -> bytes:
    aes = AES.new(key, AES.MODE_CBC, iv)
    decrypted = aes.decrypt(ciphertext)
    return unpad(decrypted)

def decode_protobuf(encoded_data: bytes, message_type: message.Message) -> message.Message:
    instance = message_type()
    try:
        instance.ParseFromString(encoded_data)
    except Exception as e:
        print(f"Parse error: {e}, data length: {len(encoded_data)}")
        raise
    return instance

async def json_to_proto(json_data: str, proto_message: Message) -> bytes:
    json_format.ParseDict(json.loads(json_data), proto_message)
    return proto_message.SerializeToString()

def get_account_credentials(region: str) -> str:
    region = region.upper()
    if region in ACCOUNT_CREDENTIALS:
        cred = ACCOUNT_CREDENTIALS[region]
        return f"uid={cred['uid']}&password={cred['password']}"
    # ফ্যালব্যাক
    return "uid=4269013803&password=MG24_GAMER_XSBOS_BY_SPIDEERIO_GAMING_TE5NG"

def get_region_config(region: str) -> dict:
    region = region.upper()
    if region in REGION_CONFIG:
        return REGION_CONFIG[region]
    # ফ্যালব্যাক
    return {"server_url": "https://loginbp.ggpolarbear.com", "release_version": "OB54"}

# === Token Generation ===

async def get_access_token(region: str):
    account = get_account_credentials(region)
    url = "https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant"
    payload = account + "&response_type=token&client_type=2&client_secret=2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3&client_id=100067"
    headers = {'User-Agent': USERAGENT, 'Connection': "Keep-Alive", 'Accept-Encoding': "gzip", 'Content-Type': "application/x-www-form-urlencoded"}
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, data=payload, headers=headers)
        data = resp.json()
        return data.get("access_token", "0"), data.get("open_id", "0")

async def create_jwt(region: str):
    region = region.upper()
    config = get_region_config(region)
    release_version = config.get("release_version", "OB54")
    
    account = get_account_credentials(region)
    token_val, open_id = await get_access_token(region)
    
    body = json.dumps({"open_id": open_id, "open_id_type": "4", "login_token": token_val, "orign_platform_type": "4"})
    proto_bytes = await json_to_proto(body, FreeFire_pb2.LoginReq())
    payload = aes_cbc_encrypt(MAIN_KEY, MAIN_IV, proto_bytes)
    
    url = f"{config['server_url']}/MajorLogin"
    headers = {'User-Agent': USERAGENT, 'Connection': "Keep-Alive", 'Accept-Encoding': "gzip",
               'Content-Type': "application/octet-stream", 'Expect': "100-continue", 'X-Unity-Version': "2018.4.11f1",
               'X-GA': "v1 1", 'ReleaseVersion': release_version}
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, data=payload, headers=headers)
        
        try:
            # ডিক্রিপ্ট করার চেষ্টা করুন
            decrypted_data = aes_cbc_decrypt(MAIN_KEY, MAIN_IV, resp.content)
            msg = json.loads(json_format.MessageToJson(decode_protobuf(decrypted_data, FreeFire_pb2.LoginRes)))
        except Exception as e:
            print(f"Decrypt failed for {region}, trying raw: {e}")
            # র ডেটা চেষ্টা করুন
            msg = json.loads(json_format.MessageToJson(decode_protobuf(resp.content, FreeFire_pb2.LoginRes)))
        
        cached_tokens[region] = {
            'token': f"Bearer {msg.get('token','0')}",
            'region': msg.get('lockRegion', region),
            'server_url': msg.get('serverUrl', 'https://ff.garena.com'),
            'expires_at': time.time() + 25200
        }

async def initialize_tokens():
    tasks = [create_jwt(r) for r in ACCOUNT_CREDENTIALS.keys()]
    await asyncio.gather(*tasks)

async def refresh_tokens_periodically():
    while True:
        await asyncio.sleep(25200)
        await initialize_tokens()

async def get_token_info(region: str) -> Tuple[str,str,str]:
    region = region.upper()
    info = cached_tokens.get(region)
    if info and time.time() < info['expires_at']:
        return info['token'], info['region'], info['server_url']
    await create_jwt(region)
    info = cached_tokens[region]
    return info['token'], info['region'], info['server_url']

async def GetAccountInformation(uid, unk, region, endpoint):
    payload = await json_to_proto(json.dumps({'a': uid, 'b': unk}), main_pb2.GetPlayerPersonalShow())
    data_enc = aes_cbc_encrypt(MAIN_KEY, MAIN_IV, payload)
    token, lock, server = await get_token_info(region)
    
    # রিজন কনফিগ থেকে release_version নিন
    config = get_region_config(region)
    release_version = config.get("release_version", "OB54")
    
    headers = {'User-Agent': USERAGENT, 'Connection': "Keep-Alive", 'Accept-Encoding': "gzip",
               'Content-Type': "application/octet-stream", 'Expect': "100-continue",
               'Authorization': token, 'X-Unity-Version': "2018.4.11f1", 'X-GA': "v1 1",
               'ReleaseVersion': release_version}
    async with httpx.AsyncClient() as client:
        resp = await client.post(server+endpoint, data=data_enc, headers=headers)
        try:
            decrypted_data = aes_cbc_decrypt(MAIN_KEY, MAIN_IV, resp.content)
            return json.loads(json_format.MessageToJson(decode_protobuf(decrypted_data, AccountPersonalShow_pb2.AccountPersonalShowInfo)))
        except:
            return json.loads(json_format.MessageToJson(decode_protobuf(resp.content, AccountPersonalShow_pb2.AccountPersonalShowInfo)))

# === Caching Decorator ===

def cached_endpoint(ttl=300):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*a, **k):
            key = (request.path, tuple(request.args.items()))
            if key in cache:
                return cache[key]
            res = fn(*a, **k)
            cache[key] = res
            return res
        return wrapper
    return decorator

# === Flask Routes ===

@app.route('/shappno')
@cached_endpoint()
def get_account_info():
    uid = request.args.get('uid')
    region_param = request.args.get('region')
    
    if not uid:
        return jsonify({"error": "Please provide UID."}), 400
    
    # যদি রিজন প্যারামিটার দেওয়া থাকে
    if region_param:
        region = region_param.upper()
        if region in ACCOUNT_CREDENTIALS:
            try:
                return_data = asyncio.run(GetAccountInformation(uid, "7", region, "/GetPlayerPersonalShow"))
                uid_region_cache[uid] = region
                formatted_json = json.dumps(return_data, indent=2, ensure_ascii=False)
                return formatted_json, 200, {'Content-Type': 'application/json; charset=utf-8'}
            except Exception as e:
                return jsonify({"error": f"Failed for region {region}: {str(e)}"}), 500
        else:
            return jsonify({"error": f"Unsupported region: {region_param}"}), 400
    
    # চেক cached region for UID
    if uid in uid_region_cache:
        try:
            return_data = asyncio.run(GetAccountInformation(uid, "7", uid_region_cache[uid], "/GetPlayerPersonalShow"))
            formatted_json = json.dumps(return_data, indent=2, ensure_ascii=False)
            return formatted_json, 200, {'Content-Type': 'application/json; charset=utf-8'}
        except:
            pass  # fallback to testing all regions
    
    # সব রিজন ট্রাই করুন
    for region in ACCOUNT_CREDENTIALS.keys():
        try:
            return_data = asyncio.run(GetAccountInformation(uid, "7", region, "/GetPlayerPersonalShow"))
            uid_region_cache[uid] = region
            formatted_json = json.dumps(return_data, indent=2, ensure_ascii=False)
            return formatted_json, 200, {'Content-Type': 'application/json; charset=utf-8'}
        except Exception as e:
            print(f"Failed for region {region}: {e}")
            continue
    
    return jsonify({"error": "UID not found in any region."}), 404

@app.route('/regions', methods=['GET'])
def get_regions():
    """সাপোর্টেড রিজনের লিস্ট দেখায়"""
    return jsonify({
        "supported_regions": list(ACCOUNT_CREDENTIALS.keys()),
        "region_config": REGION_CONFIG
    })

@app.route('/refresh', methods=['GET','POST'])
def refresh_tokens_endpoint():
    try:
        asyncio.run(initialize_tokens())
        return jsonify({'message':'Tokens refreshed for all regions.'}),200
    except Exception as e:
        return jsonify({'error': f'Refresh failed: {e}'}),500

@app.route('/token-status', methods=['GET'])
def token_status():
    """টোকেনের স্ট্যাটাস দেখায়"""
    status = {}
    for region, info in cached_tokens.items():
        if info and 'expires_at' in info:
            remaining = max(0, info['expires_at'] - time.time())
            status[region] = {
                'valid': info['expires_at'] > time.time(),
                'expires_in': f"{int(remaining // 3600)}h {int((remaining % 3600) // 60)}m",
                'region': info.get('region', 'unknown'),
                'server_url': info.get('server_url', 'unknown')
            }
    return jsonify(status)

# === Startup ===

async def startup():
    print("🔄 Initializing tokens for all regions...")
    await initialize_tokens()
    print("✅ Tokens initialized successfully!")
    asyncio.create_task(refresh_tokens_periodically())

# 🔥 Vercel এর জন্য - এইটা যোগ করো
if __name__ == '__main__':
    asyncio.run(startup())
    app.run(host='0.0.0.0', port=5000)