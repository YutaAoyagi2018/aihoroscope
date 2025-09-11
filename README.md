# Aihoroscope Web App(Django + Swiss Ephemeris + OpenAI API)

このリポジトリは、Djangoで構築した占星術サイトのソースコードです。  
本プロジェクトは **Swiss Ephemeris** を利用して天体計算を行い、さらに **OpenAI API** によって占星術解釈文を自動生成しています。

## 概要

- フレームワーク: [Django](https://www.djangoproject.com/)
- 言語: Python 3.x
- 天体計算: [Swiss Ephemeris](https://www.astro.com/swisseph/swephinfo_e.htm)
- 文章生成: [OpenAI API](https://platform.openai.com/)
- 占星術のホロスコープ計算と自動解釈を提供するWebアプリケーション

## 必要環境

- Python 3.9以上
- Django 4.x以上
- Swiss Ephemeris (ライブラリとデータファイル)
- OpenAI APIキー（利用者自身で取得）

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

## AIによる占い解釈について

本アプリは占星術の計算に加えて、文章生成の一部に **OpenAI API** を利用しています。

- ホロスコープの解釈文や性格分析の自動生成に使用  
- OpenAI APIキーはこのリポジトリには含まれていません  
- 実行する場合は、ご自身で OpenAI のアカウントを作成し、APIキーを環境変数 `OPENAI_API_KEY` に設定してください  

## 注意点

- このリポジトリには機密情報（APIキー、パスワード等）は含まれていません。  
- 実運用時には `settings.py` の **SECRET_KEY** や **DB接続情報** を環境変数で設定してください。  
- OpenAI APIキーも同様に環境変数で管理してください。  

## 謝辞
- [Swiss Ephemeris](https://www.astro.com/swisseph/) by Astrodienst AG  
- [OpenAI](https://openai.com/)  
- [Django Software Foundation](https://www.djangoproject.com/foundation/)  
- 占星術に関心を持ってくださるすべての方々
