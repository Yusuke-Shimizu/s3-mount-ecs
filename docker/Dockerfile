# jrottenberg/ffmpegイメージを基本イメージとして使用
FROM jrottenberg/ffmpeg:4.1-ubuntu

# 必要なツールのインストール
RUN apt-get update && apt-get install -y wget sudo

# mount-s3のDEBをダウンロード
RUN wget https://s3.amazonaws.com/mountpoint-s3-release/latest/x86_64/mount-s3.deb

# mount-s3のインストール
RUN sudo apt-get install -y ./mount-s3.deb

# Pythonのインストール
RUN apt-get install -y python3 python3-pip

# boto3をインストール
RUN pip3 install boto3

# 作業ディレクトリを設定
WORKDIR /app

# アプリケーションのコードをコピー
COPY . /app

# コマンドを実行
CMD ["python3", "app.py"]

ENTRYPOINT []
