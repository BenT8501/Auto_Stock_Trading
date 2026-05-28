from __future__ import annotations


THEME_KEYWORDS = {
    "반도체": {
        "terms": [
            "반도체",
            "semiconductor",
            "chip",
            "memory",
            "nvidia",
            "broadcom",
            "micron",
            "amd",
            "intel",
            "qualcomm",
            "lam research",
            "applied materials",
            "kla",
            "texas instruments",
            "analog devices",
            "sk하이닉스",
            "삼성전자",
            "삼성전기",
            "한미반도체",
            "리노공업",
            "이오테크닉스",
            "hpsp",
            "동진쎄미켐",
        ],
        "symbols": [
            "NVDA",
            "AVGO",
            "MU",
            "AMD",
            "INTC",
            "QCOM",
            "LRCX",
            "AMAT",
            "KLAC",
            "TXN",
            "ADI",
            "005930",
            "000660",
            "009150",
            "042700",
            "058470",
            "039030",
            "403870",
            "005290",
        ],
    },
    "ai": {
        "terms": [
            "ai",
            "artificial intelligence",
            "nvidia",
            "microsoft",
            "alphabet",
            "google",
            "meta",
            "amazon",
            "broadcom",
            "palantir",
            "salesforce",
            "oracle",
            "adobe",
            "삼성전자",
            "sk하이닉스",
            "네이버",
            "카카오",
        ],
        "symbols": ["NVDA", "MSFT", "GOOGL", "GOOG", "META", "AMZN", "AVGO", "PLTR", "CRM", "ORCL", "ADBE", "005930", "000660", "035420", "035720"],
    },
    "인공지능": {
        "terms": ["ai"],
        "symbols": [],
        "alias": "ai",
    },
    "전기차": {
        "terms": ["electric vehicle", "ev", "tesla", "자동차", "배터리", "2차전지", "현대차", "기아"],
        "symbols": ["TSLA", "GM", "F", "005380", "000270", "373220", "051910", "006400", "096770", "247540", "003670"],
    },
    "배터리": {
        "terms": ["battery", "2차전지", "배터리", "lg에너지솔루션", "lg화학", "삼성sdi", "sk이노베이션", "에코프로", "포스코퓨처엠"],
        "symbols": ["373220", "051910", "006400", "096770", "247540", "003670", "005490"],
    },
    "2차전지": {
        "terms": ["배터리"],
        "symbols": [],
        "alias": "배터리",
    },
    "자동차": {
        "terms": ["auto", "automotive", "car", "tesla", "현대차", "기아", "현대모비스"],
        "symbols": ["TSLA", "GM", "F", "005380", "000270", "012330"],
    },
    "바이오": {
        "terms": ["bio", "biotech", "pharma", "health", "셀트리온", "삼성바이오", "유한양행", "sk바이오팜"],
        "symbols": ["LLY", "JNJ", "UNH", "MRK", "ABBV", "PFE", "TMO", "ABT", "BMY", "SYK", "207940", "068270", "000100", "326030"],
    },
    "헬스케어": {
        "terms": ["바이오"],
        "symbols": [],
        "alias": "바이오",
    },
    "금융": {
        "terms": ["bank", "financial", "finance", "insurance", "증권", "은행", "금융", "kb금융", "신한지주", "하나금융", "우리금융"],
        "symbols": ["JPM", "BAC", "WFC", "C", "AXP", "GS", "MS", "SCHW", "BLK", "BX", "105560", "055550", "086790", "316140", "003550", "005940"],
    },
    "은행": {
        "terms": ["금융"],
        "symbols": [],
        "alias": "금융",
    },
    "에너지": {
        "terms": ["energy", "oil", "gas", "정유", "에너지", "exxon", "chevron", "sk이노베이션", "s-oil"],
        "symbols": ["XOM", "CVX", "COP", "NEE", "096770", "010950"],
    },
    "방산": {
        "terms": ["defense", "aerospace", "방산", "항공우주", "한화에어로스페이스", "l3harris", "lockheed"],
        "symbols": ["LMT", "RTX", "BA", "012450", "047810", "064350"],
    },
    "우주항공": {
        "terms": ["방산"],
        "symbols": [],
        "alias": "방산",
    },
    "조선": {
        "terms": ["shipbuilding", "조선", "중공업", "hd현대중공업", "삼성중공업", "한화오션"],
        "symbols": ["329180", "010140", "042660", "009540"],
    },
    "인터넷": {
        "terms": ["internet", "platform", "search", "social", "naver", "kakao", "alphabet", "meta"],
        "symbols": ["GOOGL", "GOOG", "META", "035420", "035720"],
    },
    "플랫폼": {
        "terms": ["인터넷"],
        "symbols": [],
        "alias": "인터넷",
    },
    "클라우드": {
        "terms": ["cloud", "aws", "azure", "google cloud", "oracle", "salesforce"],
        "symbols": ["MSFT", "AMZN", "GOOGL", "GOOG", "ORCL", "CRM"],
    },
    "소비재": {
        "terms": ["consumer", "retail", "walmart", "costco", "home depot", "coca-cola", "pepsi", "mcdonald", "starbucks"],
        "symbols": ["WMT", "COST", "HD", "KO", "PEP", "MCD", "SBUX", "PG", "LOW", "TJX"],
    },
    "리테일": {
        "terms": ["소비재"],
        "symbols": [],
        "alias": "소비재",
    },
    "통신": {
        "terms": ["telecom", "communication", "verizon", "t-mobile", "at&t", "통신"],
        "symbols": ["VZ", "TMUS", "T", "017670", "030200", "032640"],
    },
    "게임": {
        "terms": ["game", "gaming", "엔씨", "크래프톤", "넷마블", "nintendo"],
        "symbols": ["036570", "259960", "251270", "NFLX"],
    },
    "엔터": {
        "terms": ["entertainment", "media", "disney", "netflix", "하이브", "엔터"],
        "symbols": ["DIS", "NFLX", "352820", "035900", "041510"],
    },
    "철강": {
        "terms": ["steel", "철강", "posco", "포스코"],
        "symbols": ["005490", "003670"],
    },
    "건설": {
        "terms": ["construction", "건설", "현대건설", "삼성물산", "두산에너빌리티"],
        "symbols": ["000720", "028260", "034020"],
    },
}


def expand_theme(keyword: str) -> dict[str, list[str]]:
    key = str(keyword).strip().lower()
    for theme, values in THEME_KEYWORDS.items():
        if key == theme.lower():
            if values.get("alias"):
                return expand_theme(str(values["alias"]))
            return values
    return {"terms": [keyword], "symbols": []}
