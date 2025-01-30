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
HOUSE_SYSTEM = b'P'

ZODIAC_SIGNS = [
    "牡羊座", "牡牛座", "双子座", "蟹座", "獅子座", "乙女座",
    "天秤座", "蠍座", "射手座", "山羊座", "水瓶座", "魚座"
]

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

ASPECTS = {
    "コンジャンクション": 0,
    "セクスタイル": 60,
    "スクエア": 90,
    "トライン": 120,
    "オポジション": 180
}
ORB = 8


# ========== ユーティリティ関数たち ==========

def get_sign(degree: float):
    """経度(degree)から星座を判定し、(星座名, その星座内の度数) を返す。"""
    sign_index = int(degree // 30) % 12
    sign_name = ZODIAC_SIGNS[sign_index]
    degree_in_sign = degree % 30
    return sign_name, degree_in_sign


def get_house(longitude: float, cusps: list[float]) -> int:
    """longitudeがどのハウスに属するかを返す。(1~12)"""
    for i in range(12):
        start = cusps[i]
        end = cusps[(i + 1) % 12]
        if start < end:
            if start <= longitude < end:
                return i + 1
        else:
            if start <= longitude or longitude < end:
                return i + 1
    return 12  # 万が一判定できなかった場合のフォールバック


def format_position(deg_in_sign: float, sign: str) -> str:
    """度数(float) + 星座名を 'X°YY\' 星座' 形式にフォーマット。"""
    deg_int = int(deg_in_sign)
    minutes = int(round((deg_in_sign - deg_int) * 60))
    return f"{deg_int}°{minutes:02d}' {sign}"


def analyze_horoscope_data(data: dict) -> dict:
    """
    raw_data (swissephで計算した結果) を解析し、
    星座/ハウス/アスペクトなどをまとめた dict を返す。
    """
    house_cusps = data["houses"].get("cusp", [])

    # 天体の経度情報を取り出し(ASC,MCを含む)
    celestial_bodies = {
        "アセンダント": data["houses"].get("ASC", 0.0),
        "ミッドヘヴン": data["houses"].get("MC", 0.0),
        "太陽":   data["planets"].get("Sun", {}).get("longitude", [0.0])[0],
        "月":     data["planets"].get("Moon", {}).get("longitude", [0.0])[0],
        "水星":   data["planets"].get("Mercury", {}).get("longitude", [0.0])[0],
        "金星":   data["planets"].get("Venus", {}).get("longitude", [0.0])[0],
        "火星":   data["planets"].get("Mars", {}).get("longitude", [0.0])[0],
        "木星":   data["planets"].get("Jupiter", {}).get("longitude", [0.0])[0],
        "土星":   data["planets"].get("Saturn", {}).get("longitude", [0.0])[0],
        "天王星": data["planets"].get("Uranus", {}).get("longitude", [0.0])[0],
        "海王星": data["planets"].get("Neptune", {}).get("longitude", [0.0])[0],
        "冥王星": data["planets"].get("Pluto", {}).get("longitude", [0.0])[0],
        "北ノード": data["nodes"].get("True Node", {}).get("longitude", [0.0])[0],
        "リリス":  data["lilith"].get("Oscu Apogee(True Lilith)", {}).get("longitude", [0.0])[0]
    }

    # 0~360度に正規化
    celestial_bodies = {k: v % 360 for k, v in celestial_bodies.items()}

    # 1) 惑星の星座
    celestial_positions = {}
    for body, degree in celestial_bodies.items():
        sign_name, deg_in_sign = get_sign(degree)
        celestial_positions[body] = {
            "degree": degree,
            "sign": sign_name,
            "deg_in_sign": deg_in_sign,
            "formatted": format_position(deg_in_sign, sign_name)
        }

    # 2) 惑星のハウス
    celestial_houses = {}
    for body, info in celestial_positions.items():
        if body in ["アセンダント", "ミッドヘヴン"]:
            celestial_houses[body] = "-"
        else:
            h = get_house(info["degree"], house_cusps)
            celestial_houses[body] = h

    # ハウスごとの支配星を計算
    house_cusps_signs = []
    for i in range(12):
        cusp_deg = house_cusps[i] % 360
        cusp_sign, _ = get_sign(cusp_deg)
        house_cusps_signs.append(cusp_sign)

    def get_house_ruler(house_num: int, cusp_signs: list[str]) -> str:
        sign_of_house = cusp_signs[house_num - 1]
        return RULERSHIP.get(sign_of_house, "不明")

    house_rulers = {i: get_house_ruler(i, house_cusps_signs) for i in range(1, 13)}

    # 3) アスペクト計算
    planet_list = ["太陽", "月", "水星", "金星", "火星", "木星", "土星", "天王星", "海王星", "冥王星"]
    aspect_results = []
    for p1, p2 in combinations(planet_list, 2):
        deg1 = celestial_bodies[p1]
        deg2 = celestial_bodies[p2]
        angle = fabs(deg1 - deg2)
        angle = angle if angle <= 180 else 360 - angle

        for asp_name, asp_angle in ASPECTS.items():
            diff = fabs(angle - asp_angle)
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

    return {
        "1.惑星の星座": celestial_positions,
        "2.惑星のハウス": celestial_houses,
        "3.ハウスの支配星": house_rulers,
        "4.アスペクトの結果": aspect_results
    }


def compute_horoscope(year: int, month: int, day: int,
                      hour: int, minute: int,
                      lat: float, lon: float,
                      tz: float, dst: float) -> dict:
    """
    スイスエフェメリスを用いてホロスコープを計算し、
    解析結果をまとめた辞書({ "raw_data": {...}, "analysis": {...} })を返す。
    """

    # ローカル時刻 -> UT(世界時) 変換
    ut = (hour + minute / 60.0) - (tz + dst)

    # ユリウス日(JD) を計算 (グレゴリオ暦指定)
    jd_ut = swe.julday(year, month, day, ut, swe.GREG_CAL)

    # 主要天体の位置計算 (太陽～冥王星)
    planets_info = {}
    for planet_code in range(swe.SUN, swe.PLUTO + 1):
        try:
            lon_p, lat_p = swe.calc_ut(jd_ut, planet_code, swe.FLG_SWIEPH)
            planet_name = swe.get_planet_name(planet_code)
            planets_info[planet_name] = {
                "longitude": lon_p,
                "latitude": lat_p
            }
        except Exception as e:
            planet_name = swe.get_planet_name(planet_code)
            planets_info[planet_name] = {"error": str(e)}

    # ノード(ドラゴンヘッド)
    nodes_codes = [
        ("Mean Node", swe.MEAN_NODE),
        ("True Node", swe.TRUE_NODE),
    ]
    nodes_info = {}
    for node_name, node_code in nodes_codes:
        try:
            lon_n, lat_n = swe.calc_ut(jd_ut, node_code, swe.FLG_SWIEPH)
            nodes_info[node_name] = {
                "longitude": lon_n,
                "latitude": lat_n
            }
        except Exception as e:
            nodes_info[node_name] = {"error": str(e)}

    # リリス(ブラックムーン)
    lilith_codes = [
        ("Mean Apogee(Lilith)", swe.MEAN_APOG),
        ("Oscu Apogee(True Lilith)", swe.OSCU_APOG),
    ]
    lilith_info = {}
    for lilith_name, lilith_code in lilith_codes:
        try:
            lon_l, lat_l = swe.calc_ut(jd_ut, lilith_code, swe.FLG_SWIEPH)
            lilith_info[lilith_name] = {
                "longitude": lon_l,
                "latitude": lat_l
            }
        except Exception as e:
            lilith_info[lilith_name] = {"error": str(e)}

    # ハウス(ASC, MC, 12ハウスカスプ) を計算
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

    # (1) raw_data としてまとめる
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

    # (2) 分析(星座/ハウス/アスペクト)
    analysis_result = analyze_horoscope_data(raw_data)

    # (3) 返却
    return {
        "raw_data": raw_data,
        "analysis": analysis_result
    }
