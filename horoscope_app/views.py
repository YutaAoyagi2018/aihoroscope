# horoscope_app/views.py
import os
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
# CSRF保護デコレータ
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import ValidationError
import datetime
from zoneinfo import ZoneInfo
import copy
import uuid
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseForbidden

# OpenAI
from openai import OpenAI

# 上で作成したユーティリティ関数をインポート
from .utils import compute_horoscope

def index(request):
    """
    トップページ(index.html)を返すビュー。
    ユーザがここでフォームに出生データを入力する。
    """
    years = range(1900, 2100)
    months = range(1, 13)
    days = range(1, 32)
    # ワンタイムトークン生成
    token = str(uuid.uuid4())
    request.session['valid_token'] = token

    context = {
        'years': years,
        'months': months,
        'days': days,
        'token': token,  # テンプレートに渡す
    }
    return render(request, 'horoscope_app/index.html', context)

def compatibility(request):
    """
    二人の相性(compatibility.html)を返すビュー。
    ユーザがここでフォームに出生データを入力する。
    """
    years = range(1900, 2100)
    months = range(1, 13)
    days = range(1, 32)
    return render(request, 'horoscope_app/compatibility.html', {'years': years, 'months': months, 'days': days})


def horoscope(request):
    """
    GETパラメータからホロスコープを計算して JSON を返すAPIエンドポイント。

    例:
      /horoscope?year=2025&month=1&day=29&hour=14&minute=30
        &lat=35.6895&lon=139.6917&tz=9.0&dst=0.0
    """
    if request.method != "GET":
        return JsonResponse({"error": "Invalid request method. GETのみ対応しています。"}, status=400)

    # GETから各値を取得
    try:
        year = int(request.GET.get("year", "2023"))
        month = int(request.GET.get("month", "1"))
        day = int(request.GET.get("day", "1"))
        hour = int(request.GET.get("hour", "0"))
        minute = int(request.GET.get("minute", "0"))
        lat = float(request.GET.get("lat", "35.6895"))
        lon = float(request.GET.get("lon", "139.6917"))
        tz = float(request.GET.get("tz", "9.0"))
        dst = float(request.GET.get("dst", "0.0"))
        prefecture = request.GET.get('prefecture', 'Tokyo')
    except ValueError as ve:
        return JsonResponse({"error": "Invalid input parameters", "details": str(ve)}, status=400)

    try:
        input_date = datetime.datetime(year, month, day)
        if input_date < datetime.datetime(1900, 1, 1) or input_date > datetime.datetime(2100, 12, 31):
            raise ValidationError("日付は1900年1月1日から2100年12月31日までの範囲で入力してください。")
    except ValidationError as ve:
        return JsonResponse({"error": str(ve)}, status=400)
    except Exception as e:
        return JsonResponse({"error": "日付の解析に失敗しました。"}, status=400)
    

    # ユーティリティ関数で計算
    result_dict = compute_horoscope(year, month, day, hour, minute, lat, lon, tz, dst, prefecture)
    
    # JSONとして返す
    return JsonResponse(result_dict)


@csrf_protect
def analyze(request):
    """
    POSTで受け取った出生データを使い、ホロスコープを計算→OpenAI で占いコメントを生成→返す。
    """
    if request.method != "POST":
        return JsonResponse({"error": "POSTメソッドのみ対応しています。"}, status=400)

    data = request.POST

    try:
        year = int(request.POST.get("year", "2023"))
        month = int(request.POST.get("month", "1"))
        day = int(request.POST.get("day", "1"))
        hour = int(request.POST.get("hour", "0"))
        minute = int(request.POST.get("minute", "0"))
        lat = float(request.POST.get("lat", "35.6895"))
        lon = float(request.POST.get("lon", "139.6917"))
        tz = float(request.POST.get("tz", "9.0"))
        dst = float(request.POST.get("dst", "0.0"))
        sb = int(request.POST.get("sb", "1"))
        prefecture = request.POST.get('prefecture', 'Tokyo')
        unknown_str = request.POST.get("unknown", "false").lower()
        unknown = unknown_str == "on"
    except (ValueError, TypeError):
        return JsonResponse({"error": "入力データに誤りがあります。"}, status=400)
    
    try:
        input_date = datetime.datetime(year, month, day)
        if input_date < datetime.datetime(1900, 1, 1) or input_date > datetime.datetime(2100, 12, 31):
            raise ValidationError("日付は1900年1月1日から2100年12月31日までの範囲で入力してください。")
    except ValidationError as ve:
        return JsonResponse({"error": str(ve)}, status=400)
    except Exception as e:
        return JsonResponse({"error": "日付の解析に失敗しました。"}, status=400)
    

    # (1) ホロスコープ計算
    
    result_dict = compute_horoscope(year, month, day, hour, minute, lat, lon, tz, dst, prefecture)
    
    horoscope_data = result_dict.get("analysis", {})
    

    # (2) ChatGPTへ送るプロンプト作成
    horoscope_str = json.dumps(horoscope_data, ensure_ascii=False, indent=2)
    user_message = "あなたは熟練した占星術師であり、日本語で丁寧に分かりやすく回答を行います。\n"
    if sb == 1:
        user_message += (
            "以下のネイタルチャートを参考に、性格を教えてください。\n"
            "【ネイタルチャート】\n"
            f"{horoscope_str}\n\n"
            "この人の性格はどのようになっていると考えられますか？\n"
            f"400字程度で結論だけ教えてください。\n"
        )
    elif sb == 2:
        user_message += (
            "以下のネイタルチャートを参考に、恋愛運を教えてください。\n"
            "【ネイタルチャート】\n"
            f"{horoscope_str}\n\n"
            "この人の恋愛運はどのようになっていると考えられますか？\n"
            f"400字程度で結論だけ教えてください。\n"
        )
    elif sb == 3:
        user_message += (
            "以下のネイタルチャートを参考に、仕事運を教えてください。\n"
            "【ネイタルチャート】\n"
            f"{horoscope_str}\n\n"
            "この人の仕事運はどのようになっていると考えられますか？\n"
            f"400字程度で結論だけ教えてください。\n"
        )
    elif sb == 4:
        user_message += (
            "以下のネイタルチャートを参考に、金運を教えてください。\n"
            "【ネイタルチャート】\n"
            f"{horoscope_str}\n\n"
            "この人の金運はどのようになっていると考えられますか？\n"
            f"400字程度で結論だけ教えてください。\n"
        )
    elif sb == 5:
        user_message += (
            "以下のネイタルチャートを参考に、健康運を教えてください。\n"
            "【ネイタルチャート】\n"
            f"{horoscope_str}\n\n"
            "この人の健康運はどのようになっていると考えられますか？\n"
            f"400字程度で結論だけ教えてください。\n"
        )
    elif sb == 6:
        user_message += (
            "以下のネイタルチャートを参考に、学業運を教えてください。\n"
            "【ネイタルチャート】\n"
            f"{horoscope_str}\n\n"
            "この人の学業運はどのようになっていると考えられますか？\n"
            f"400字程度で結論だけ教えてください。\n"
        )
    elif sb == 9:
        tokyo_now = datetime.datetime.now(ZoneInfo("Asia/Tokyo"))
        today = tokyo_now.date()
        year_t = today.year
        month_t = today.month
        day_t = today.day
        result_dict = compute_horoscope(year_t, month_t, day_t, 12, 0, lat, lon, tz, dst, prefecture)
        transit_data = result_dict.get("analysis", {}).get("1.天体の配置")
        filtered_dict = {key: value for key, value in transit_data.items() if key not in ['アセンダント', 'ミッドヘヴェン']}
        transit_str = json.dumps(filtered_dict, ensure_ascii=False, indent=2)
        user_message += (
            f"以下のネイタルチャートとトランジットの惑星データを参考に、アスペクトも計算して、今日（{year_t}年{month_t}月{day_t}日）の運勢を教えてください。\n"
            "【ネイタルチャート】\n"
            f"{horoscope_str}\n\n"
            "【トランジットの惑星】\n"
            f"{transit_str}\n\n"
            f"この人の今日（{year_t}年{month_t}月{day_t}日）の運勢はどのようになっていると考えられますか？\n"
            f"400字程度で結論だけ教えてください。\n"
        )
    elif sb == 10:
        tokyo_now = datetime.datetime.now(ZoneInfo("Asia/Tokyo"))
        today = tokyo_now.date()
        year_t = today.year

        # 各月のトランジットデータを格納する辞書を初期化
        transit_str = {}

        for month in range(1, 13):
            # 各月のホロスコープを計算
            horoscope_result = compute_horoscope(year_t, month, 1, 12, 0, lat, lon, tz, dst, prefecture)
            result_dict[month] = horoscope_result

            # トランジットデータの抽出と不要なキーの除外
            transit_data = horoscope_result.get("analysis", {}).get("1.天体の配置", {})
            filtered = {k: v for k, v in transit_data.items() if k not in ['アセンダント', 'ミッドヘヴェン']}
            transit_str[month] = json.dumps(filtered, ensure_ascii=False, indent=2)

        # 各月のトランジットデータの文字列を生成
        transit_messages = "\n\n".join(
            [f"【トランジットの惑星{month}月】\n{transit_str[month]}" for month in range(1, 13)]
        )

        # ユーザーメッセージの生成
        user_message += (
            f"以下のネイタルチャートとトランジットの惑星データを参考に、アスペクトも計算して、今年（{year_t}年）の運勢を教えてください。\n"
            f"【ネイタルチャート】\n{horoscope_str}\n\n"
            f"{transit_messages}\n\n"
            f"トランジットの特に外惑星との関係から、この人の今年（{year_t}年）の運勢はどのようになっていると考えられますか？\n"
            f"400字程度で結論だけ教えてください。\n"
        )
    elif sb == 11:
        user_message += (
            "以下のネイタルチャートを参考に、性格を教えてください。\n"
            "【ネイタルチャート】\n"
            f"{horoscope_str}\n\n"
            "この人の性格はどのようになっていると考えられますか？\n"
        )
    elif sb == 12:
        user_message += (
            "以下のネイタルチャートを参考に、恋愛運を教えてください。\n"
            "【ネイタルチャート】\n"
            f"{horoscope_str}\n\n"
            "この人の恋愛運はどのようになっていると考えられますか？\n"
        )
    elif sb == 13:
        user_message += (
            "以下のネイタルチャートを参考に、仕事運を教えてください。\n"
            "【ネイタルチャート】\n"
            f"{horoscope_str}\n\n"
            "この人の仕事運はどのようになっていると考えられますか？\n"
        )
    elif sb == 14:
        user_message += (
            "以下のネイタルチャートを参考に、金運を教えてください。\n"
            "【ネイタルチャート】\n"
            f"{horoscope_str}\n\n"
            "この人の金運はどのようになっていると考えられますか？\n"
        )
    elif sb == 15:
        user_message += (
            "以下のネイタルチャートを参考に、健康運を教えてください。\n"
            "【ネイタルチャート】\n"
            f"{horoscope_str}\n\n"
            "この人の健康運はどのようになっていると考えられますか？\n"
        )
    elif sb == 16:
        user_message += (
            "以下のネイタルチャートを参考に、学業運を教えてください。\n"
            "【ネイタルチャート】\n"
            f"{horoscope_str}\n\n"
            "この人の学業運はどのようになっていると考えられますか？\n"
        )
    elif sb == 19:
        tokyo_now = datetime.datetime.now(ZoneInfo("Asia/Tokyo"))
        today = tokyo_now.date()
        year_t = today.year
        month_t = today.month
        day_t = today.day
        result_dict = compute_horoscope(year_t, month_t, day_t, 12, 0, lat, lon, tz, dst, prefecture)
        transit_data = result_dict.get("analysis", {}).get("1.天体の配置")
        filtered_dict = {key: value for key, value in transit_data.items() if key not in ['アセンダント', 'ミッドヘヴェン']}
        transit_str = json.dumps(filtered_dict, ensure_ascii=False, indent=2)
        user_message += (
            f"以下のネイタルチャートとトランジットの惑星データを参考に、アスペクトも計算して、今日（{year_t}年{month_t}月{day_t}日）の運勢を教えてください。\n"
            "【ネイタルチャート】\n"
            f"{horoscope_str}\n\n"
            "【トランジットの惑星】\n"
            f"{transit_str}\n\n"
            f"この人の今日（{year_t}年{month_t}月{day_t}日）の運勢はどのようになっていると考えられますか？\n"
        )
    elif sb == 20:
        tokyo_now = datetime.datetime.now(ZoneInfo("Asia/Tokyo"))
        today = tokyo_now.date()
        year_t = today.year

        # 各月のトランジットデータを格納する辞書を初期化
        transit_str = {}

        for month in range(1, 13):
            # 各月のホロスコープを計算
            horoscope_result = compute_horoscope(year_t, month, 1, 12, 0, lat, lon, tz, dst, prefecture)
            result_dict[month] = horoscope_result

            # トランジットデータの抽出と不要なキーの除外
            transit_data = horoscope_result.get("analysis", {}).get("1.天体の配置", {})
            filtered = {k: v for k, v in transit_data.items() if k not in ['アセンダント', 'ミッドヘヴェン']}
            transit_str[month] = json.dumps(filtered, ensure_ascii=False, indent=2)

        # 各月のトランジットデータの文字列を生成
        transit_messages = "\n\n".join(
            [f"【トランジットの惑星{month}月】\n{transit_str[month]}" for month in range(1, 13)]
        )

        # ユーザーメッセージの生成
        user_message += (
            f"以下のネイタルチャートとトランジットの惑星データを参考に、アスペクトも計算して、今年（{year_t}年）の運勢を教えてください。\n"
            f"【ネイタルチャート】\n{horoscope_str}\n\n"
            f"{transit_messages}\n\n"
            f"トランジットの特に外惑星との関係から、この人の今年（{year_t}年）の運勢はどのようになっていると考えられますか？\n"
        )


    if unknown:
        user_message += "出生時刻が不明なので、アセンダント、MC、ハウスのデータは使わないでください。"

    # (3) OpenAI APIキーを取得し、ChatCompletionを呼び出し
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        return JsonResponse({"error": "OpenAI APIキーが設定されていません。"}, status=500)

    client = OpenAI(api_key=OPENAI_API_KEY)

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                # {"role": "system", "content": "あなたは熟練した占星術師であり、日本語で丁寧に分かりやすく回答を行います。"},
                {"role": "user", "content": user_message},
            ],
            model="gpt-4o-2024-11-20",  # 必要に応じてモデル名を修正
            timeout=180,
            # temperature=0.7,
            # max_tokens=1500
        )
        answer = chat_completion.choices[0].message.content
    except Exception as e:
        return JsonResponse({"error": f"OpenAI APIの呼び出しに失敗: {e}"}, status=500)

    # (4) 結果を返す
    return JsonResponse({"result": answer})

@csrf_protect
def analyze_compatibility(request):
    """
    POSTで受け取った出生データを使い、ホロスコープを計算→OpenAI で占いコメントを生成→返す。
    """
    if request.method != "POST":
        return JsonResponse({"error": "POSTメソッドのみ対応しています。"}, status=400)

    data = request.POST

    try:
        year1 = int(request.POST.get("year1", "2023"))
        month1 = int(request.POST.get("month1", "1"))
        day1 = int(request.POST.get("day1", "1"))
        hour1 = int(request.POST.get("hour1", "0"))
        minute1 = int(request.POST.get("minute1", "0"))
        lat1 = float(request.POST.get("lat1", "35.6895"))
        lon1 = float(request.POST.get("lon1", "139.6917"))
        tz1 = float(request.POST.get("tz1", "9.0"))
        dst1 = float(request.POST.get("dst1", "0.0"))
        prefecture1 = request.POST.get('prefecture1', 'Tokyo')
        unknown_str1 = request.POST.get("unknown1", "false").lower()
        unknown1 = unknown_str1 == "on"
        
        year2 = int(request.POST.get("year2", "2023"))
        month2 = int(request.POST.get("month2", "1"))
        day2 = int(request.POST.get("day2", "1"))
        hour2 = int(request.POST.get("hour2", "0"))
        minute2 = int(request.POST.get("minute2", "0"))
        lat2 = float(request.POST.get("lat2", "35.6895"))
        lon2 = float(request.POST.get("lon2", "139.6917"))
        tz2 = float(request.POST.get("tz2", "9.0"))
        dst2 = float(request.POST.get("dst2", "0.0"))
        prefecture2 = request.POST.get('prefecture2', 'Tokyo')
        unknown_str2 = request.POST.get("unknown2", "false").lower()
        unknown2 = unknown_str2 == "on"
        
        sb = int(request.POST.get("sb", "1"))
        


    except (ValueError, TypeError):
        return JsonResponse({"error": "入力データに誤りがあります。"}, status=400)
    
    try:
        input_date = datetime.datetime(year1, month1, day1)
        if input_date < datetime.datetime(1900, 1, 1) or input_date > datetime.datetime(2100, 12, 31):
            raise ValidationError("日付は1900年1月1日から2100年12月31日までの範囲で入力してください。")
    except ValidationError as ve:
        return JsonResponse({"error": str(ve)}, status=400)
    except Exception as e:
        return JsonResponse({"error": "日付の解析に失敗しました。"}, status=400)
    

    # (1) ホロスコープ計算
    result_dict1 = compute_horoscope(year1, month1, day1, hour1, minute1, lat1, lon1, tz1, dst1, prefecture1)
    result_dict2 = compute_horoscope(year2, month2, day2, hour2, minute2, lat2, lon2, tz2, dst2, prefecture2)
    horoscope_data1 = result_dict1.get("analysis", {})
    horoscope_data2 = result_dict2.get("analysis", {})

    # (2) ChatGPTへ送るプロンプト作成
    horoscope_str1 = json.dumps(horoscope_data1, ensure_ascii=False, indent=2)
    horoscope_str2 = json.dumps(horoscope_data2, ensure_ascii=False, indent=2)
    
    user_message = "あなたは熟練した占星術師であり、日本語で丁寧に分かりやすく回答を行います。\n"
    if sb == 7:
        user_message += (
            "以下のネイタルチャートを参考に、二人の相性を教えてください。\n"
            "【私のネイタルチャート】\n"
            f"{horoscope_str1}\n\n\n\n"
            "【お相手のネイタルチャート】\n"
            f"{horoscope_str2}\n\n"
            "この二人の相性はどのようになっていると考えられますか？\n"
        )
    elif sb == 8:
        user_message += (
            "以下のネイタルチャートを参考に、二人の今後を教えてください。\n"
            "【私のネイタルチャート】\n"
            f"{horoscope_str1}\n\n\n\n"
            "【お相手のネイタルチャート】\n"
            f"{horoscope_str2}\n\n"
            "この二人の今後はどのようになっていると考えられますか？\n"
        )

    if unknown1 == True and unknown2 == False:
        user_message += "私の出生時刻が不明なので、私のアセンダント、MC、ハウスのデータは使わないでください。"
    elif unknown1 == False and unknown2 == True:
        user_message += "お相手の出生時刻が不明なので、お相手のアセンダント、MC、ハウスのデータは使わないでください。"
    elif unknown1 == True and unknown2 == True:
        user_message += "二人の出生時刻が不明なので、アセンダント、MC、ハウスのデータは使わないでください。"


    # (3) OpenAI APIキーを取得し、ChatCompletionを呼び出し
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        return JsonResponse({"error": "OpenAI APIキーが設定されていません。"}, status=500)

    client = OpenAI(api_key=OPENAI_API_KEY)

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                # {"role": "system", "content": "あなたは熟練した占星術師であり、日本語で丁寧に分かりやすく回答を行います。"},
                {"role": "user", "content": user_message},
            ],
            model="gpt-4o-2024-11-20",  # 必要に応じてモデル名を修正
            timeout=180,
            # temperature=0.7,
            # max_tokens=1500
        )
        answer = chat_completion.choices[0].message.content
    except Exception as e:
        return JsonResponse({"error": f"OpenAI APIの呼び出しに失敗: {e}"}, status=500)

    # (4) 結果を返す
    return JsonResponse({"result": answer})


def horoscope_detail(request):

    if request.method != "GET":
        return JsonResponse({"error": "Invalid request method. GETのみ対応しています。"}, status=400)

    # GETから各値を取得
    try:
        year = int(request.GET.get("year", "2023"))
        month = int(request.GET.get("month", "1"))
        day = int(request.GET.get("day", "1"))
        hour = int(request.GET.get("hour", "0"))
        minute = int(request.GET.get("minute", "0"))
        lat = float(request.GET.get("lat", "35.6895"))
        lon = float(request.GET.get("lon", "139.6917"))
        tz = float(request.GET.get("tz", "9.0"))
        dst = float(request.GET.get("dst", "0.0"))
        prefecture = request.GET.get('prefecture', 'Tokyo')
    except ValueError as ve:
        return JsonResponse({"error": "Invalid input parameters", "details": str(ve)}, status=400)

    try:
        input_date = datetime.datetime(year, month, day)
        if input_date < datetime.datetime(1900, 1, 1) or input_date > datetime.datetime(2100, 12, 31):
            raise ValidationError("日付は1900年1月1日から2100年12月31日までの範囲で入力してください。")
    except ValidationError as ve:
        return JsonResponse({"error": str(ve)}, status=400)
    except Exception as e:
        return JsonResponse({"error": "日付の解析に失敗しました。"}, status=400)
    

    # ユーティリティ関数で計算
    result_dict = compute_horoscope(year, month, day, hour, minute, lat, lon, tz, dst, prefecture)

    # JSONとして返す
    data = result_dict

    merged_planets = []
    for planet, z_info in data["analysis"]["1.天体の配置"].items():
        clean_planet = planet.strip()
        h_info = data["analysis"]["2.惑星のハウス"].get(clean_planet, None)
        merged_planets.append({
            "planet": clean_planet,
            "zodiac_formatted": z_info["formatted"],
            "house": h_info
        })
    
    merged_house_data = []
    for cusp in data["analysis"]["8.ハウスカスプ"]:
        # 「house」番号を取り出し
        house_number = cusp["house"]
        # house_ruler の中から該当の「支配星」を取得（存在しない場合は None）
        ruler = data["analysis"]["3.ハウスの支配星"].get(house_number, None)

        merged_house_data.append({
            "house": house_number,
            "cusp_formatted": cusp["formatted"],
            "ruler": ruler
        })

    # テンプレートに渡すコンテキストを作成
    context = {
        'zodiac_info': data["analysis"]["1.天体の配置"],
        'house_info': data["analysis"]["2.惑星のハウス"],
        'house_ruler': data["analysis"]["3.ハウスの支配星"],
        'aspects': data["analysis"]["4.アスペクトの結果"],
        'four_elements': data["analysis"]["5.天体の四区分"],
        'three_modes': data["analysis"]["6.天体の三区分"],
        'two_polarities': data["analysis"]["7.天体の二区分"],
        'house_cusps': data["analysis"]["8.ハウスカスプ"],
        'marged_planets': merged_planets,
        'merged_house_data': merged_house_data,
    }
    return render(request, 'horoscope_app/horoscope_detail.html', context)


def horoscope_ai(request):
    """
    GETパラメータからホロスコープを計算して JSON を返すAPIエンドポイント。

    例:
      /horoscope?year=2025&month=1&day=29&hour=14&minute=30
        &lat=35.6895&lon=139.6917&tz=9.0&dst=0.0
    """
    if request.method != "GET":
        return JsonResponse({"error": "Invalid request method. GETのみ対応しています。"}, status=400)

    # トークン検証
    token = request.GET.get('token')
    valid_token = request.session.get('valid_token')

    if not (token and valid_token and token == valid_token):
        return HttpResponseForbidden('Forbidden: 無効なトークンです。')

    # トークンは使い捨て
    del request.session['valid_token']
    # GETから各値を取得
    try:
        year = int(request.GET.get("year", "2023"))
        month = int(request.GET.get("month", "1"))
        day = int(request.GET.get("day", "1"))
        hour = int(request.GET.get("hour", "0"))
        minute = int(request.GET.get("minute", "0"))
        lat = float(request.GET.get("lat", "35.6895"))
        lon = float(request.GET.get("lon", "139.6917"))
        tz = float(request.GET.get("tz", "9.0"))
        dst = float(request.GET.get("dst", "0.0"))
        prefecture = request.GET.get('prefecture', 'Tokyo')
    except ValueError as ve:
        return JsonResponse({"error": "Invalid input parameters", "details": str(ve)}, status=400)

    try:
        input_date = datetime.datetime(year, month, day)
        if input_date < datetime.datetime(1900, 1, 1) or input_date > datetime.datetime(2100, 12, 31):
            raise ValidationError("日付は1900年1月1日から2100年12月31日までの範囲で入力してください。")
    except ValidationError as ve:
        return JsonResponse({"error": str(ve)}, status=400)
    except Exception as e:
        return JsonResponse({"error": "日付の解析に失敗しました。"}, status=400)
    

    # ユーティリティ関数で計算
    result_dict = compute_horoscope(year, month, day, hour, minute, lat, lon, tz, dst, prefecture)
    
    result_dict = result_dict["analysis"]


    # 元のデータを壊さないように、深いコピーを作成する
    result_copy = copy.deepcopy(result_dict)

    # 天体の配置のformattedだけを抽出
    result_copy["1.天体の配置"] = {
        planet: data["formatted"]
        for planet, data in result_dict["1.天体の配置"].items()
    }

    # ハウスカスプのformattedだけを抽出
    result_copy["8.ハウスカスプ"] = [
        cusp["formatted"] for cusp in result_dict["8.ハウスカスプ"]
    ]

    # JSONとして返す
    return JsonResponse(result_copy)
