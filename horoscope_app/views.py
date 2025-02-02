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
    return render(request, 'horoscope_app/index.html', {'years': years, 'months': months, 'days': days})



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
        year   = int(request.GET.get("year",   "2023"))
        month  = int(request.GET.get("month",  "1"))
        day    = int(request.GET.get("day",    "1"))
        hour   = int(request.GET.get("hour",   "0"))
        minute = int(request.GET.get("minute", "0"))
        lat    = float(request.GET.get("lat",  "35.6895"))
        lon    = float(request.GET.get("lon",  "139.6917"))
        tz     = float(request.GET.get("tz",   "9.0"))
        dst    = float(request.GET.get("dst",  "0.0"))
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
    result_dict = compute_horoscope(year, month, day, hour, minute, lat, lon, tz, dst)

    # JSONとして返す
    return JsonResponse(result_dict)


@csrf_protect
def analyze(request):
    """
    POSTで受け取った出生データを使い、ホロスコープを計算→OpenAI で解析コメントを生成→返す。
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
    result_dict = compute_horoscope(year, month, day, hour, minute, lat, lon, tz, dst)
    horoscope_data = result_dict.get("analysis", {})

    # (2) ChatGPTへ送るプロンプト作成
    horoscope_str = json.dumps(horoscope_data, ensure_ascii=False, indent=2)
    user_message = "あなたは熟練した占星術師であり、日本語で丁寧に分かりやすく回答を行います。\n"
    if sb == 1:
        user_message += (
            "以下のホロスコープ解析データを参考に、性格を教えてください。\n"
            "【ホロスコープデータ】\n"
            f"{horoscope_str}\n\n"
            "この人の性格はどのようになっていると考えられますか？\n"
        )
    elif sb == 2:
        user_message += (
            "以下のホロスコープ解析データを参考に、恋愛運を教えてください。\n"
            "【ホロスコープデータ】\n"
            f"{horoscope_str}\n\n"
            "この人の恋愛運はどのようになっていると考えられますか？\n"
        )
    elif sb == 3:
        user_message += (
            "以下のホロスコープ解析データを参考に、仕事運を教えてください。\n"
            "【ホロスコープデータ】\n"
            f"{horoscope_str}\n\n"
            "この人の仕事運はどのようになっていると考えられますか？\n"
        )
    elif sb == 4:
        user_message += (
            "以下のホロスコープ解析データを参考に、金運を教えてください。\n"
            "【ホロスコープデータ】\n"
            f"{horoscope_str}\n\n"
            "この人の金運はどのようになっていると考えられますか？\n"
        )
    elif sb == 5:
        user_message += (
            "以下のホロスコープ解析データを参考に、健康運を教えてください。\n"
            "【ホロスコープデータ】\n"
            f"{horoscope_str}\n\n"
            "この人の健康運はどのようになっていると考えられますか？\n"
        )
    elif sb == 6:
        user_message += (
            "以下のホロスコープ解析データを参考に、学業運を教えてください。\n"
            "【ホロスコープデータ】\n"
            f"{horoscope_str}\n\n"
            "この人の学業運はどのようになっていると考えられますか？\n"
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
            model="o1-mini",  # 必要に応じてモデル名を修正
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
        year   = int(request.GET.get("year",   "2023"))
        month  = int(request.GET.get("month",  "1"))
        day    = int(request.GET.get("day",    "1"))
        hour   = int(request.GET.get("hour",   "0"))
        minute = int(request.GET.get("minute", "0"))
        lat    = float(request.GET.get("lat",  "35.6895"))
        lon    = float(request.GET.get("lon",  "139.6917"))
        tz     = float(request.GET.get("tz",   "9.0"))
        dst    = float(request.GET.get("dst",  "0.0"))
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
    result_dict = compute_horoscope(year, month, day, hour, minute, lat, lon, tz, dst)

    # JSONとして返す
    data = result_dict

    merged_planets = []
    for planet, z_info in data["analysis"]["1.惑星の星座"].items():
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
        'zodiac_info': data["analysis"]["1.惑星の星座"],
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
