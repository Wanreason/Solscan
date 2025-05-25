import requests

API_ENDPOINTS = {
    "openocean": "https://apis.openocean.finance/developer/apis/meme-api",
    "bitquery": "https://coinpedia.org/top-10/top-10-solana-blockchain-apis-for-developers/",
    "mcp": "https://github.com/tony-42069/solana-mcp"
}

def get_trending_memecoins():
    memecoins = []
    for name, url in API_ENDPOINTS.items():
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()  # Raise error for bad responses (e.g., 404, 500)
            data = response.json()
            memecoins.extend(data.get("tokens", []))  # Adjust based on API response format
        except requests.exceptions.RequestException as e:
            print(f"❌ API error for {name}: {e}")
            continue
    return memecoins

def filter_scams(memecoins):
    return [coin for coin in memecoins if coin.get("trust_score", 0) > 80]
