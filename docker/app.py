import boto3
import subprocess
import json
import os


def mount_s3(bucket_name, mount_point):
    # マウント先ディレクトリを作成（存在しない場合）
    subprocess.run(['mkdir', '-p', mount_point])

    # S3バケットをマウント
    result = subprocess.run(['mount-s3', bucket_name, mount_point])

    if result.returncode != 0:
        print('S3バケットのマウントに失敗しました')
        return False
    else:
        print('S3バケットのマウントに成功しました')

        # マウントしたディレクトリの中身を表示
        print('ディレクトリの中身:')
        with os.scandir(mount_point) as entries:
            for entry in entries:
                print(entry.name)

        return True

def list_buckets():
    # boto3クライアントの作成
    s3 = boto3.client('s3')
    
    # S3バケットの一覧表示
    response = s3.list_buckets()
    buckets = [bucket['Name'] for bucket in response['Buckets']]
    print("Available Buckets:", buckets)

def list_bucket_contents(bucket_name):
    # boto3クライアントの作成
    s3 = boto3.client('s3')
    
    # 指定したバケットの中身をリストアップ
    objects = s3.list_objects_v2(Bucket=bucket_name)
    
    if 'Contents' not in objects:
        print(f"No objects in bucket {bucket_name}")
        return

    print(f"Objects in bucket {bucket_name}:")
    for obj in objects['Contents']:
        print(obj['Key'])

def get_video_duration(file_path):
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        file_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        print(f'Error running ffprobe: {result.stderr.decode()}')
        return None

    return float(result.stdout.decode().strip())

print("hoge")
# 上記の関数を呼び出してマウント操作を実行
if __name__ == '__main__':
    print("main")
    BUCKET_NAME = os.environ.get("BUCKET_NAME")
    if BUCKET_NAME is None:
        raise EnvironmentError("必要な環境変数が設定されていません。")

    list_bucket_contents(BUCKET_NAME)

    mount_point = '/app/hoge'  # マウント先ディレクトリ
    mount_s3(BUCKET_NAME, mount_point)
    
    # 動画ファイルのパス
    file_path = mount_point + '/video.mp4'
    video_duration = get_video_duration(file_path)
    
    if video_duration is not None:
        print(f'Video Duration: {video_duration} seconds')
    else:
        print('Failed to retrieve video duration')
