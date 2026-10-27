# ============================================================
#  app.py — Free Fire Info API (Full rewrite)
# ============================================================

import asyncio
import time
import json
import base64
import os
from collections import defaultdict
from functools import wraps

import httpx
from flask import Flask, request, jsonify
from flask_cors import CORS
from cachetools import TTLCache
from Crypto.Cipher import AES
from google.protobuf import json_format, message
from google.protobuf.message import Message
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder

# ============================================================
#  Proto: FreeFire_pb2 (LoginReq + LoginRes) — inline
# ============================================================
_sym_db = _symbol_database.Default()
_FF_DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\x0e\x46reeFire.proto"c\n\x08LoginReq\x12\x0f\n\x07open_id\x18\x16 \x01(\t'
    b'\x12\x14\n\x0copen_id_type\x18\x17 \x01(\t\x12\x13\n\x0blogin_token\x18\x1d '
    b'\x01(\t\x12\x1b\n\x13orign_platform_type\x18\x63 \x01(\t"]\n\x10\x42lacklist'
    b'InfoRes\x12\x1e\n\nban_reason\x18\x01 \x01(\x0e\x32\n.BanReason\x12\x17\n'
    b'\x0f\x65xpire_duration\x18\x02 \x01(\r\x12\x10\n\x08\x62\x61n_time\x18\x03 '
    b'\x01(\r"f\n\x0eLoginQueueInfo\x12\r\n\x05\x61llow\x18\x01 \x01(\x08\x12'
    b'\x16\n\x0equeue_position\x18\x02 \x01(\r\x12\x16\n\x0eneed_wait_secs\x18'
    b'\x03 \x01(\r\x12\x15\n\rqueue_is_full\x18\x04 \x01(\x08"\xa0\x03\n\x08'
    b'LoginRes\x12\x12\n\naccount_id\x18\x01 \x01(\x04\x12\x13\n\x0block_region'
    b'\x18\x02 \x01(\t\x12\x13\n\x0bnoti_region\x18\x03 \x01(\t\x12\x11\n\tip_'
    b'region\x18\x04 \x01(\t\x12\x19\n\x11\x61gora_environment\x18\x05 \x01(\t'
    b'\x12\x19\n\x11new_active_region\x18\x06 \x01(\t\x12\x19\n\x11recommend_'
    b'regions\x18\x07 \x03(\t\x12\r\n\x05token\x18\x08 \x01(\t\x12\x0b\n\x03ttl'
    b'\x18\t \x01(\r\x12\x12\n\nserver_url\x18\n \x01(\t\x12\x16\n\x0e\x65mul'
    b'ator_score\x18\x0b \x01(\r\x12$\n\tblacklist\x18\x0c \x01(\x0b\x32\x11.'
    b'BlacklistInfoRes\x12#\n\nqueue_info\x18\r \x01(\x0b\x32\x0f.LoginQueue'
    b'Info\x12\x0e\n\x06tp_url\x18\x0e \x01(\t\x12\x15\n\rapp_server_id\x18'
    b'\x0f \x01(\r\x12\x0f\n\x07\x61no_url\x18\x10 \x01(\t\x12\x0f\n\x07ip_city'
    b'\x18\x11 \x01(\t\x12\x16\n\x0eip_subdivision\x18\x12 \x01(\t*\xa8\x01\n'
    b'\tBanReason\x12\x16\n\x12\x42\x41N_REASON_UNKNOWN\x10\x00\x12\x1b\n\x17'
    b'\x42\x41N_REASON_IN_GAME_AUTO\x10\x01\x12\x15\n\x11\x42\x41N_REASON_'
    b'REFUND\x10\x02\x12\x15\n\x11\x42\x41N_REASON_OTHERS\x10\x03\x12\x16\n'
    b'\x12\x42\x41N_REASON_SKINMOD\x10\x04\x12 \n\x1b\x42\x41N_REASON_IN_GAME'
    b'_AUTO_NEW\x10\xf6\x07\x62\x06proto3'
)
_g = globals()
_builder.BuildMessageAndEnumDescriptors(_FF_DESCRIPTOR, _g)
_builder.BuildTopDescriptorsAndMessages(_FF_DESCRIPTOR, "FreeFire_pb2", _g)
LoginReq = _g["LoginReq"]
LoginRes = _g["LoginRes"]

# ============================================================
#  Proto: main_pb2 + AccountPersonalShow_pb2 — inline
#  (نفس الملفات القديمة — لا تغيير)
# ============================================================
_MAIN_DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\nmain.proto";\n\x15GetPlayerPersonalShow\x12\x0c\n\x04open\x18\x01 \x01('
    b'\x04\x12\x14\n\x0caccount_id\x18\x02 \x01(\r\x62\x06proto3'
)
_builder.BuildMessageAndEnumDescriptors(_MAIN_DESCRIPTOR, _g)
_builder.BuildTopDescriptorsAndMessages(_MAIN_DESCRIPTOR, "main_pb2", _g)
GetPlayerPersonalShow = _g["GetPlayerPersonalShow"]

_APS_DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\x17\x41\x63\x63ountPersonalShow.proto"\x94\x01\n\x17\x41\x63\x63ountPersonal'
    b'ShowInfo\x12\x12\n\naccount_id\x18\x01 \x01(\x04\x12\x10\n\x08nickname\x18'
    b'\x02 \x01(\t\x12\r\n\x05level\x18\x03 \x01(\r\x12\x0b\n\x03\x65xp\x18\x04 '
    b'\x01(\x04\x12\x12\n\nregion\x18\x05 \x01(\t\x12\x0e\n\x06is_bot\x18\x06 '
    b'\x01(\x08\x12\x13\n\x0bcreate_time\x18\x07 \x01(\x04\x62\x06proto3'
)
_builder.BuildMessageAndEnumDescriptors(_APS_DESCRIPTOR, _g)
_builder.BuildTopDescriptorsAndMessages(_APS_DESCRIPTOR, "AccountPersonalShow_pb2", _g)
AccountPersonalShowInfo = _g["AccountPersonalShowInfo"]

# ============================================================
#  Constants
# ============================================================
MAIN_KEY = base64.b64decode("WWcmdGMlREV1aDYlWmNeOA==")
MAIN_IV  = base64.b64decode("Nm95WkRyMjJFM3ljaGpNJQ==")
RELEASEVERSION = "OB55"
USERAGENT = "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)"
LOGIN_URL = "https://loginbp.ppmainecoonghj.com/"

# ============================================================
#  Accounts (env vars أولاً — fallback للـ hardcoded)
# ============================================================
def _acc(region, default_uid, default_pass):
    uid = os.getenv(f"{region}_UID", default_uid)
    pwd = os.getenv(f"{region}_PASSWORD", default_pass)
    return {"uid": uid, "password": pwd}

ACCOUNT_CREDENTIALS = {
    "BD":  _acc("BD",  "5372860087", "shappno_create-by-shappno_S7kkYNMy"),
    "IND": _acc("IND", "4269013803", "MG24_GAMER_XSBOS_BY_SPIDEERIO_GAMING_TE5NG"),
    "ME":  _acc("ME",  "4269012488", "MG24_GAMER_U27YB_BY_SPIDEERIO_GAMING_0PNCN"),
    "SG":  _acc("SG",  "4269012488", "MG24_GAMER_U27YB_BY_SPIDEERIO_GAMING_0PNCN"),
    "ID":  _acc("ID",  "4269012488", "MG24_GAMER_U27YB_BY_SPIDEERIO_GAMING_0PNCN"),
    "TH":  _acc("TH",  "4269012488", "MG24_GAMER_U27YB_BY_SPIDEERIO_GAMING_0PNCN"),
    "VN":  _acc("VN",  "4269012488", "MG24_GAMER_U27YB_BY_SPIDEERIO_GAMING_0PNCN"),
    "PK":  _acc("PK",  "4269012488", "MG24_GAMER_U27YB_BY_SPIDEERIO_GAMING_0PNCN"),
    "BR":  _acc("BR",  "4269012488", "MG24_GAMER_U27YB_BY_SPIDEERIO_GAMING_0PNCN"),
    "US":  _acc("US",  "4269012488", "MG24_GAMER_U27YB_BY_SPIDEERIO_GAMING_0PNCN"),
    "EU":  _acc("EU",  "4269012488", "MG24_GAMER_U27YB_BY_SPIDEERIO_GAMING_0PNCN"),
}

REGION_CONFIG = {
    "BD":  {"server_url": LOGIN_URL, "release_version": RELEASEVERSION},
    "IND": {"server_url": LOGIN_URL, "release_version": RELEASEVERSION},
    "ME":  {"server_url": LOGIN_URL, "release_version": RELEASEVERSION},
    "SG":  {"server_url": LOGIN_URL, "release_version": RELEASEVERSION},
    "ID":  {"server_url": LOGIN_URL, "release_version": RELEASEVERSION},
    "TH":  {"server_url": LOGIN_URL, "release_version": RELEASEVERSION},
    "VN":  {"server_url": LOGIN_URL, "release_version": RELEASEVERSION},
    "PK":  {"server_url": LOGIN_URL, "release_version": RELEASEVERSION},
    "BR":  {"server_url": LOGIN_URL, "release_version": RELEASEVERSION},
    "US":  {"server_url": LOGIN_URL, "release_version": RELEASEVERSION},
    "EU":  {"server_url": LOGIN_URL, "release_version": RELEASEVERSION},
}

# ============================================================
#  Flask App
# ============================================================
app = Flask(__name__)
CORS(app)
cache = TTLCache(maxsize=100, ttl=300)
cached_tokens = defaultdict(dict)
uid_region_cache = {}

# ============================================================
#  AES + Proto helpers
# ============================================================
def _pad(t: bytes) -> bytes:
    n = AES.block_size - (len(t) % AES.block_size)
    return t + bytes([n] * n)

def _unpad(t: bytes) -> bytes:
    if not t:
        return t
    n = t[-1]
    if n < 1 or n > AES.block_size:
        return t
    return t[:-n]

def _aes_enc(pt: bytes) -> bytes:
    return AES.new(MAIN_KEY, AES.MODE_CBC, MAIN_IV).encrypt(_pad(pt))

def _aes_dec(ct: bytes) -> bytes:
    return _unpad(AES.new(MAIN_KEY, AES.MODE_CBC, MAIN_IV).decrypt(ct))

def _decode_proto(data: bytes, msg_type):
    m = msg_type()
    m.ParseFromString(data)
    return m

# ============================================================
#  Major Login (sync — نشغلها عبر executor)
# ============================================================
_client = httpx.Client(
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=50),
    timeout=httpx.Timeout(15.0, connect=5.0),
    verify=False,
)

def _try_parse_loginres(data: bytes):
    try:
        m = LoginRes()
        m.ParseFromString(data)
        if m.account_id and m.account_id > 0:
            return json.loads(json_format.MessageToJson(m))
    except Exception:
        pass
    return None

def _extract_loginres(raw: bytes) -> dict:
    p = _try_parse_loginres(raw)
    if p:
        return p

    i = 0
    while True:
        i = raw.find(b"\x08", i)
        if i == -1:
            break
        p = _try_parse_loginres(raw[i:])
        if p:
            return p
        i += 1

    j = raw.find(b"eyJhbGciOiJIUzI1NiIs")
    if j != -1:
        for k in range(j - 1, max(j - 300, -1), -1):
            if raw[k] == 0x42:
                p = _try_parse_loginres(raw[k:])
                if p:
                    return p
                break

    raise Exception(
        f"Could not parse LoginRes. len={len(raw)}, first={raw[:20].hex()}"
    )

def major_login(uid: str, password: str) -> dict:
    # 1) Garena guest token
    r = _client.post(
        "https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant",
        data={
            "uid": str(uid),
            "password": str(password),
            "response_type": "token",
            "client_type": "2",
            "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
            "client_id": "100067",
        },
        headers={
            "User-Agent": USERAGENT,
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    ).json()

    access_token = r.get("access_token")
    open_id = r.get("open_id")
    if not access_token or not open_id:
        raise Exception(f"Invalid credentials / token grant failed: {r}")

    # 2) Build LoginReq
    msg = LoginReq()
    json_format.ParseDict(
        {
            "open_id": open_id,
            "open_id_type": "4",
            "login_token": access_token,
            "orign_platform_type": "4",
        },
        msg,
    )

    payload = _aes_enc(msg.SerializeToString())

    # 3) POST /MajorLogin
    resp = _client.post(
        f"{LOGIN_URL}MajorLogin",
        data=payload,
        headers={
            "User-Agent": USERAGENT,
            "Accept": "*/*",
            "Accept-Encoding": "deflate, gzip",
            "X-Ga-Sv": "1789534056",
            "Authorization": "Bearer",
            "X-Ga": "v1 1",
            "Releaseversion": RELEASEVERSION,
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Unity-Version": "2018.4.12f1",
            "PlAy_VeR": "1.132.1",
            "Ob_VeR": RELEASEVERSION,
        },
    )

    if resp.status_code != 200:
        raise Exception(
            f"MajorLogin HTTP {resp.status_code}: {resp.text[:200]}"
        )

    res = _extract_loginres(resp.content)
    return {
        "jwt_token": res.get("token"),
        "account_id": res.get("accountId"),
        "region": res.get("lockRegion") or res.get("notiRegion"),
        "server_url": res.get("serverUrl"),
        "open_id": open_id,
        "access_token": access_token,
        "raw": res,
    }

# ============================================================
#  Token cache & refresh (async)
# ============================================================
async def create_jwt(region: str):
    region = region.upper()
    cred = ACCOUNT_CREDENTIALS.get(region)
    if not cred:
        raise Exception(f"No credentials for region {region}")

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, major_login, cred["uid"], cred["password"]
    )

    cached_tokens[region] = {
        "token": f"Bearer {result['jwt_token']}",
        "region": result["region"] or region,
        "server_url": result["server_url"] or LOGIN_URL,
        "expires_at": time.time() + 25200,
    }
    return cached_tokens[region]

async def initialize_tokens():
    tasks = [create_jwt(r) for r in ACCOUNT_CREDENTIALS.keys()]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for r, res in zip(ACCOUNT_CREDENTIALS.keys(), results):
        if isinstance(res, Exception):
            print(f"[init] {r} failed: {res}")
        else:
            print(f"[init] {r} OK")

async def get_token_info(region: str):
    region = region.upper()
    info = cached_tokens.get(region)
    if info and time.time() < info["expires_at"]:
        return info["token"], info["region"], info["server_url"]
    await create_jwt(region)
    info = cached_tokens[region]
    return info["token"], info["region"], info["server_url"]

# ============================================================
#  GetPlayerPersonalShow
# ============================================================
async def get_account_information(uid, unk, region, endpoint):
    req = GetPlayerPersonalShow()
    json_format.ParseDict({"open": int(uid), "account_id": int(uid)}, req)
    # ملاحظة: لو الـ proto الأصلي بياخد أ/ب، غيّر dict فوق حسب الحقول الفعلية
    data_enc = _aes_enc(req.SerializeToString())

    token, lock, server = await get_token_info(region)
    cfg = REGION_CONFIG.get(region.upper(), {"release_version": RELEASEVERSION})

    headers = {
        "User-Agent": USERAGENT,
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "Content-Type": "application/octet-stream",
        "Expect": "100-continue",
        "Authorization": token,
        "X-Unity-Version": "2018.4.12f1",
        "X-GA": "v1 1",
        "ReleaseVersion": cfg["release_version"],
    }

    async with httpx.AsyncClient(verify=False, timeout=15.0) as c:
        resp = await c.post(server + endpoint, data=data_enc, headers=headers)
        if resp.status_code != 200:
            raise Exception(f"HTTP {resp.status_code} on {endpoint}")

        try:
            decrypted = _aes_dec(resp.content)
            msg = _decode_proto(decrypted, AccountPersonalShowInfo)
        except Exception:
            msg = _decode_proto(resp.content, AccountPersonalShowInfo)

        return json.loads(json_format.MessageToJson(msg))

# ============================================================
#  Caching decorator
# ============================================================
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

# ============================================================
#  Routes
# ============================================================
@app.route("/")
def index():
    return jsonify({
        "service": "Free Fire Info API",
        "endpoints": ["/shappno?uid=...&region=...", "/regions", "/refresh", "/token-status"],
    })

@app.route("/shappno")
@cached_endpoint()
def get_account_info():
    uid = request.args.get("uid")
    region_param = request.args.get("region")

    if not uid:
        return jsonify({"error": "Please provide UID."}), 400

    if region_param:
        region = region_param.upper()
        if region not in ACCOUNT_CREDENTIALS:
            return jsonify({"error": f"Unsupported region: {region}"}), 400
        try:
            data = asyncio.run(
                get_account_information(uid, "7", region, "/GetPlayerPersonalShow")
            )
            uid_region_cache[uid] = region
            return jsonify(data), 200
        except Exception as e:
            return jsonify({"error": f"Failed for region {region}: {e}"}), 500

    if uid in uid_region_cache:
        try:
            data = asyncio.run(
                get_account_information(
                    uid, "7", uid_region_cache[uid], "/GetPlayerPersonalShow"
                )
            )
            return jsonify(data), 200
        except Exception:
            pass

    last_err = None
    for region in ACCOUNT_CREDENTIALS.keys():
        try:
            data = asyncio.run(
                get_account_information(uid, "7", region, "/GetPlayerPersonalShow")
            )
            uid_region_cache[uid] = region
            return jsonify(data), 200
        except Exception as e:
            last_err = e
            continue

    return jsonify({"error": f"UID not found. Last error: {last_err}"}), 404

@app.route("/regions")
def get_regions():
    return jsonify({
        "supported_regions": list(ACCOUNT_CREDENTIALS.keys()),
        "region_config": REGION_CONFIG,
    })

@app.route("/refresh", methods=["GET", "POST"])
def refresh_tokens_endpoint():
    try:
        asyncio.run(initialize_tokens())
        ok = [r for r, v in cached_tokens.items() if v.get("token")]
        failed = [r for r in ACCOUNT_CREDENTIALS if r not in ok]
        return jsonify({
            "message": "Tokens refreshed.",
            "ok": ok,
            "failed": failed,
        }), 200
    except Exception as e:
        return jsonify({"error": f"Refresh failed: {e}"}), 500

@app.route("/token-status")
def token_status():
    status = {}
    for region, info in cached_tokens.items():
        if info and "expires_at" in info:
            remaining = max(0, info["expires_at"] - time.time())
            status[region] = {
                "valid": info["expires_at"] > time.time(),
                "expires_in": f"{int(remaining // 3600)}h {int((remaining % 3600) // 60)}m",
                "region": info.get("region", "unknown"),
                "server_url": info.get("server_url", "unknown"),
            }
    return jsonify(status)

# ============================================================
#  Startup
# ============================================================
async def startup():
    print("🔄 Initializing tokens...")
    await initialize_tokens()
    print("✅ Done")

if __name__ == "__main__":
    asyncio.run(startup())
    app.run(host="0.0.0.0", port=5000, debug=False)
