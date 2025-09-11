# Aihoroscope Web App(Django + Swiss Ephemeris)

このリポジトリは、Djangoで構築した占星術サイトのソースコードです。  
本プロジェクトは **Swiss Ephemeris** を利用して天体計算を行っています。

## 概要

- フレームワーク: [Django](https://www.djangoproject.com/)
- 言語: Python 3.x
- 天体計算: [Swiss Ephemeris](https://www.astro.com/swisseph/swephinfo_e.htm)
- 占星術のホロスコープ計算と自動解釈を提供するWebアプリケーション

## 必要環境

- Python 3.9以上
- Django 4.x以上
- Swiss Ephemeris (ライブラリとデータファイル)

## インストール方法

```bash
# リポジトリをクローン
git clone https://github.com/YutaAoyagi2018/aihoroscope.git
cd aihoroscope

# 必要ライブラリをインストール
pip install -r requirements.txt

# データベースを初期化
python manage.py migrate

# 開発サーバー起動
python manage.py runserver
```

## ライセンス
本ソフトウェアは GNU Affero General Public License v3 (AGPL-3.0) の下で配布されます。
詳細は LICENSE をご覧ください。

あなたはこのソフトウェアを自由に利用・改変・再配布できます。

ただし、このソフトウェアをサービスとして利用者に提供する場合、必ずソースコードを公開する必要があります。

## Swiss Ephemerisについて
このアプリは Swiss Ephemeris を利用しています。
Swiss Ephemeris は Astrodienst AG が著作権を有し、AGPL または有料ライセンスの下で提供されています。
詳細は公式サイトをご覧ください:
https://www.astro.com/swisseph/

## 注意点
このリポジトリには機密情報（APIキー、パスワード等）は含まれていません。

実運用時には settings.py の SECRET_KEY や DB接続情報 を環境変数で設定してください。

## 謝辞
Swiss Ephemeris by Astrodienst AG

Django Software Foundation

占星術に関心を持ってくださるすべての方々
