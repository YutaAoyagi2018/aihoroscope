# horoscope_app/utils.py
import os
import swisseph as swe
import json
from math import fabs
from itertools import combinations

# --- Swiss Ephemeris パス設定 ---
# プロジェクトの構成に応じて、正しいパスをセットしてください。
swe.set_ephe_path(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ephe')
)

# --- 定数/星座/ルーラー/アスペクト定義 ---
HOUSE_SYSTEM = b'P'  # Placidusなど、好みに応じて変更可

ZODIAC_SIGNS = [
    "牡羊座", "牡牛座", "双子座", "蟹座",
    "獅子座", "乙女座", "天秤座", "蠍座",
    "射手座", "山羊座", "水瓶座", "魚座"
]

# 各星座のルーラー（モダンルーラー想定）
RULERSHIP = {
    "牡羊座": "火星",
    "牡牛座": "金星",
    "双子座": "水星",
    "蟹座": "月",
    "獅子座": "太陽",
    "乙女座": "水星",
    "天秤座": "金星",
    "蠍座": "冥王星",
    "射手座": "木星",
    "山羊座": "土星",
    "水瓶座": "天王星",
    "魚座": "海王星"
}

# アスペクトとオーブ
ASPECTS = {
    "コンジャンクション": 0,
    "セクスタイル": 60,
    "スクエア": 90,
    "トライン": 120,
    "オポジション": 180
}
# ORB = 8  # 全アスペクト共通のオーブ例
# アスペクト名とORB値の対応を辞書で定義
aspect_orbs = {
    "コンジャンクション": 10,
    "オポジション": 8,
    "トライン": 6,
    "スクエア": 6,
    "セクスタイル": 4,
}

# 4区分（元素）
ZODIAC_ELEMENTS = {
    "牡羊座": "火",
    "牡牛座": "地",
    "双子座": "風",
    "蟹座": "水",
    "獅子座": "火",
    "乙女座": "地",
    "天秤座": "風",
    "蠍座": "水",
    "射手座": "火",
    "山羊座": "地",
    "水瓶座": "風",
    "魚座": "水"
}

# 3区分（活動・不動・柔軟）
ZODIAC_MODES = {
    "牡羊座": "活動",
    "牡牛座": "不動",
    "双子座": "柔軟",
    "蟹座": "活動",
    "獅子座": "不動",
    "乙女座": "柔軟",
    "天秤座": "活動",
    "蠍座": "不動",
    "射手座": "柔軟",
    "山羊座": "活動",
    "水瓶座": "不動",
    "魚座": "柔軟"
}

# 2区分（陽・陰）
ZODIAC_POLARITY = {
    "牡羊座": "陽",
    "牡牛座": "陰",
    "双子座": "陽",
    "蟹座": "陰",
    "獅子座": "陽",
    "乙女座": "陰",
    "天秤座": "陽",
    "蠍座": "陰",
    "射手座": "陽",
    "山羊座": "陰",
    "水瓶座": "陽",
    "魚座": "陰"
}


# ========== ユーティリティ関数たち ==========

def get_sign(degree: float):
    """経度(degree)から星座を判定し、(星座名, その星座内の度数) を返す。"""
    sign_index = int(degree // 30) % 12
    sign_name = ZODIAC_SIGNS[sign_index]
    degree_in_sign = degree % 30
    return sign_name, degree_in_sign


def get_house(longitude: float, cusps: list[float]) -> int:
    """
    longitude (0～360) がどのハウスに属するかを返す (1~12)。
    cusps は len=12 のハウスカスプ度数リスト。
    """
    for i in range(12):
        start = cusps[i]
        end = cusps[(i + 1) % 12]
        if start < end:
            # 0°～360°を単純に区切る
            if start <= longitude < end:
                return i + 1
        else:
            # ハウスが 360° をまたぐ場合
            # 例: start=350, end=20 のとき「350 <= x < 360 or 0 <= x < 20」
            if start <= longitude or longitude < end:
                return i + 1
    return 12  # 万が一判定できなかった場合のフォールバック


def format_position(deg_in_sign: float, sign: str) -> str:
    """度数(float) + 星座名を 'X°YY\' 星座' 形式にフォーマット。"""
    deg_int = int(deg_in_sign)
    minutes = int(round((deg_in_sign - deg_int) * 60))
    return f"{deg_int}°{minutes:02d}' {sign}"


def analyze_horoscope_data(data: dict, birth_info: dict) -> dict:
    """
    raw_data (swissephで計算した結果) を解析し、
    星座/ハウス/アスペクト/4区分/3区分/2区分/ハウスカスプ度数 をまとめた dict を返す。
    """
    house_cusps = data["houses"].get("cusp", [])

    # ---------------------------
    # 1) 天体リストの抽出
    # ---------------------------
    celestial_bodies = {
        "アセンダント": {
            "longitude_0": data["houses"].get("ASC", 0.0) % 360,
            "longitude_3": 0.0  # スピードの情報がない場合は0.0等のデフォルト値
        },
        "ミッドヘヴェン": {
            "longitude_0": data["houses"].get("MC", 0.0) % 360,
            "longitude_3": 0.0
        },
        "太陽": {
            "longitude_0": data["planets"].get("Sun", {}).get("longitude", [0.0])[0] % 360,
            "longitude_3": data["planets"].get("Sun", {}).get("longitude", [0.0])[3],
        },
        "月": {
            "longitude_0": data["planets"].get("Moon", {}).get("longitude", [0.0])[0] % 360,
            "longitude_3": data["planets"].get("Moon", {}).get("longitude", [0.0])[3],
        },
        "水星": {
            "longitude_0": data["planets"].get("Mercury", {}).get("longitude", [0.0])[0] % 360,
            "longitude_3": data["planets"].get("Mercury", {}).get("longitude", [0.0])[3],
        },
        "金星": {
            "longitude_0": data["planets"].get("Venus", {}).get("longitude", [0.0])[0] % 360,
            "longitude_3": data["planets"].get("Venus", {}).get("longitude", [0.0])[3],
        },
        "火星": {
            "longitude_0": data["planets"].get("Mars", {}).get("longitude", [0.0])[0] % 360,
            "longitude_3": data["planets"].get("Mars", {}).get("longitude", [0.0])[3],
        },
        "木星": {
            "longitude_0": data["planets"].get("Jupiter", {}).get("longitude", [0.0])[0] % 360,
            "longitude_3": data["planets"].get("Jupiter", {}).get("longitude", [0.0])[3],
        },
        "土星": {
            "longitude_0": data["planets"].get("Saturn", {}).get("longitude", [0.0])[0] % 360,
            "longitude_3": data["planets"].get("Saturn", {}).get("longitude", [0.0])[3],
        },
        "天王星": {
            "longitude_0": data["planets"].get("Uranus", {}).get("longitude", [0.0])[0] % 360,
            "longitude_3": data["planets"].get("Uranus", {}).get("longitude", [0.0])[3],
        },
        "海王星": {
            "longitude_0": data["planets"].get("Neptune", {}).get("longitude", [0.0])[0] % 360,
            "longitude_3": data["planets"].get("Neptune", {}).get("longitude", [0.0])[3],
        },
        "冥王星": {
            "longitude_0": data["planets"].get("Pluto", {}).get("longitude", [0.0])[0] % 360,
            "longitude_3": data["planets"].get("Pluto", {}).get("longitude", [0.0])[3],
        },
    }

    # ---------------------------
    # 2) 各天体の星座・度数・フォーマット
    # ---------------------------
    celestial_positions = {}
    for body, info in celestial_bodies.items():
        degree = info["longitude_0"]
        speed = info["longitude_3"]
        sign_name, deg_in_sign = get_sign(degree)
        formatted = format_position(deg_in_sign, sign_name)
        if speed < 0:
            formatted += " R"
        celestial_positions[body] = {
            "degree": degree,
            "sign": sign_name,
            "deg_in_sign": deg_in_sign,
            "formatted": formatted
        }

    # ---------------------------
    # 3) 各天体のハウス
    # ---------------------------
    celestial_houses = {}
    for body, info in celestial_positions.items():
        if body in ["アセンダント", "ミッドヘヴェン"]:
            celestial_houses[body] = "-"  # ASC/MCはハウスに入れない例
        else:
            h = get_house(info["degree"], house_cusps)
            celestial_houses[body] = h

    # ---------------------------
    # 4) ハウスごとの支配星 (既存実装例)
    # ---------------------------
    house_cusps_signs = []
    for i in range(12):
        cusp_deg = house_cusps[i] % 360
        cusp_sign, _ = get_sign(cusp_deg)
        house_cusps_signs.append(cusp_sign)

    def get_house_ruler(house_num: int, cusp_signs: list[str]) -> str:
        sign_of_house = cusp_signs[house_num - 1]
        return RULERSHIP.get(sign_of_house, "不明")

    house_rulers = {i: get_house_ruler(i, house_cusps_signs) for i in range(1, 13)}

    # ---------------------------
    # 5) アスペクト計算 (例:太陽～冥王星)
    # ---------------------------
    planet_list = [
        "太陽", "月", "水星", "金星", "火星",
        "木星", "土星", "天王星", "海王星", "冥王星"
    ]
    aspect_results = []
    for p1, p2 in combinations(planet_list, 2):
        deg1 = celestial_positions[p1]["degree"]
        deg2 = celestial_positions[p2]["degree"]
        angle = fabs(deg1 - deg2)
        angle = angle if angle <= 180 else 360 - angle

        for asp_name, asp_angle in ASPECTS.items():
            diff = fabs(angle - asp_angle)
            ORB = aspect_orbs.get(asp_name, 8)
            if diff <= ORB:
                orb_diff = angle - asp_angle
                orb_sign = "+" if orb_diff >= 0 else "-"
                aspect_results.append({
                    "aspect": asp_name,
                    "planet1": p1,
                    "planet2": p2,
                    "angle": round(angle, 2),
                    "orb": round(abs(orb_diff), 2),
                    "orb_sign": orb_sign
                })

    # ---------------------------
    # 6) 天体の4区分/3区分/2区分へのグループ分け
    # ---------------------------
    four_divisions = {"火": [], "地": [], "風": [], "水": []}
    three_divisions = {"活動": [], "不動": [], "柔軟": []}
    two_divisions = {"陽": [], "陰": []}

    for body, info in celestial_positions.items():
        sign = info["sign"]  # 例: "牡羊座"
        elem = ZODIAC_ELEMENTS.get(sign, "")
        mode = ZODIAC_MODES.get(sign, "")
        pol  = ZODIAC_POLARITY.get(sign, "")

        if elem in four_divisions:
            four_divisions[elem].append(body)
        if mode in three_divisions:
            three_divisions[mode].append(body)
        if pol in two_divisions:
            two_divisions[pol].append(body)

    # ---------------------------
    # 7) ハウスカスプの星座/度数リスト追加
    # ---------------------------
    house_cusps_list = []
    for i in range(12):
        cusp_deg = house_cusps[i] % 360
        sign_name, deg_in_sign = get_sign(cusp_deg)
        house_cusps_list.append({
            "house": i + 1,
            "cusp_degree": round(cusp_deg, 2),
            "sign": sign_name,
            "deg_in_sign": round(deg_in_sign, 2),
            "formatted": format_position(deg_in_sign, sign_name)
        })

    # ---------------------------
    # 解析結果まとめ
    # ---------------------------
    return {
        "1.天体の配置": celestial_positions,      # 天体：星座・度数
        "2.惑星のハウス": celestial_houses,       # 天体が何ハウスか
        "3.ハウスの支配星": house_rulers,         # ハウスの支配星
        "4.アスペクトの結果": aspect_results,      # 惑星間のアスペクト
        "5.天体の四区分": four_divisions,
        "6.天体の三区分": three_divisions,
        "7.天体の二区分": two_divisions,
        "8.ハウスカスプ": house_cusps_list,
        "9.生年月日と出生地": birth_info  # ★ここを追加
    }


def compute_horoscope(year: int, month: int, day: int,
                      hour: int, minute: int,
                      lat: float, lon: float,
                      tz: float, dst: float, prefecture: str) -> dict:
    """
    スイスエフェメリスを用いてホロスコープを計算し、
    解析結果をまとめた辞書({ "raw_data": {...}, "analysis": {...} })を返す。
    
    :param year: 西暦年
    :param month: 月 (1-12)
    :param day: 日 (1-31)
    :param hour: 時 (0-23)
    :param minute: 分 (0-59)
    :param lat: 観測地点の緯度 (北緯は+、南緯は-)
    :param lon: 観測地点の経度 (東経は+、西経は-)
    :param tz: タイムゾーン (例: 日本は+9)
    :param dst: サマータイム補正時間 (通常0, 夏時間なら+1等)
    """
    # ---------------------------
    # 1) ローカル時刻 -> UT(世界時) 変換
    # ---------------------------
    ut = (hour + minute / 60.0) - (tz + dst)

    # ---------------------------
    # 2) ユリウス日 (JD) を計算 (グレゴリオ暦指定)
    # ---------------------------
    jd_ut = swe.julday(year, month, day, ut, swe.GREG_CAL)

    # ---------------------------
    # 3) 主要天体の位置 (太陽～冥王星) を計算
    # ---------------------------
    planets_info = {}
    flg = swe.FLG_SWIEPH | swe.FLG_SPEED
    for planet_code in range(swe.SUN, swe.PLUTO + 1):
        try:
            lon_p, lat_p = swe.calc_ut(jd_ut, planet_code, flg)
            planet_name = swe.get_planet_name(planet_code)
            planets_info[planet_name] = {
                "longitude": lon_p,
                "latitude": lat_p
            }
        except Exception as e:
            planet_name = swe.get_planet_name(planet_code)
            planets_info[planet_name] = {"error": str(e)}

    # ---------------------------
    # 4) ノード(ドラゴンヘッド) 計算
    # ---------------------------
    nodes_codes = [
        ("Mean Node", swe.MEAN_NODE),
        ("True Node", swe.TRUE_NODE),
    ]
    nodes_info = {}
    for node_name, node_code in nodes_codes:
        try:
            lon_n, lat_n = swe.calc_ut(jd_ut, node_code, flg)
            nodes_info[node_name] = {
                "longitude": lon_n,
                "latitude": lat_n
            }
        except Exception as e:
            nodes_info[node_name] = {"error": str(e)}

    # ---------------------------
    # 5) リリス(ブラックムーン) 計算
    # ---------------------------
    lilith_codes = [
        ("Mean Apogee(Lilith)", swe.MEAN_APOG),
        ("Oscu Apogee(True Lilith)", swe.OSCU_APOG),
    ]
    lilith_info = {}
    for lilith_name, lilith_code in lilith_codes:
        try:
            lon_l, lat_l = swe.calc_ut(jd_ut, lilith_code, flg)
            lilith_info[lilith_name] = {
                "longitude": lon_l,
                "latitude": lat_l
            }
        except Exception as e:
            lilith_info[lilith_name] = {"error": str(e)}

    # ---------------------------
    # 6) ハウス (ASC, MC, 12ハウスカスプ) の計算
    # ---------------------------
    try:
        houses_result = swe.houses(jd_ut, lat, lon, HOUSE_SYSTEM)
        if len(houses_result) == 2:
            cusps, ascmc = houses_result
            asc, mc = ascmc[0], ascmc[1]
            houses_info = {
                "ASC":  asc,
                "MC":   mc,
                "cusp": list(cusps),
                "ASCMC": list(ascmc)
            }
        else:
            houses_info = {
                "error": f"Houses function returned {len(houses_result)} values, expected 2.",
                "content": houses_result
            }
    except Exception as e:
        houses_info = {"error": str(e)}

    # ---------------------------
    # (1) raw_data まとめ
    # ---------------------------
    raw_data = {
        "jd_ut": jd_ut,
        "local_time": {
            "year":   year,
            "month":  month,
            "day":    day,
            "hour":   hour,
            "minute": minute,
            "tz":     tz,
            "dst":    dst,
            "ut_used": ut,
        },
        "planets": planets_info,
        "nodes":   nodes_info,
        "lilith":  lilith_info,
        "houses":  houses_info
    }
    birth_info = {
        "year": year,
        "month": month,
        "day": day,
        "hour": hour,
        "minute": minute,
        "latitude": lat,
        "longitude": lon,
        "timezone": tz,
        "dst": dst,
        "birthplace": prefecture  # prefecture（出生地）を追加
    }
    # ---------------------------
    # (2) 解析(星座/ハウス/アスペクト/4区分など)
    # ---------------------------
    analysis_result = analyze_horoscope_data(raw_data, birth_info)

    # ---------------------------
    # (3) 返却 (raw_data + analysis)
    # ---------------------------
    return {
        "analysis": analysis_result,
        "raw_data": raw_data
    }
