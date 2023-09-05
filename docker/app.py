import boto3
import subprocess
import json
import os
import logging


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


def create_media_convert_job(file_name, job_template, role_name, bucket_name, video_duration):
    # STS クライアントの作成とアカウントIDの取得
    sts_client = boto3.client('sts')
    account_id = sts_client.get_caller_identity()["Account"]

    # MediaConvert クライアントを初期化（エンドポイントを指定しない）
    region_name='ap-northeast-1'
    client = boto3.client('mediaconvert', region_name=region_name)

    try:
        # エンドポイント情報を取得
        endpoints = client.describe_endpoints()
        endpoint_url = endpoints['Endpoints'][0]['Url']
    
        client = boto3.client('mediaconvert', region_name=region_name, endpoint_url=endpoint_url)
        
        # 分割数（MaxCaptures）を定義
        max_captures = 5
        
        # video_duration を四捨五入して整数に変換
        framerate_denominator = round(video_duration)

        # MediaConvert settings
        thumnail_json = {
            'Extension': 'jpg',
            'NameModifier': '_thumbnail1',
            'ContainerSettings': {
                'Container': 'RAW'
            },
            'VideoDescription': {
                'CodecSettings': {
                    'Codec': 'FRAME_CAPTURE',
                    'FrameCaptureSettings': {
                        'FramerateNumerator': max_captures,
                        'FramerateDenominator': framerate_denominator,
                        'MaxCaptures': max_captures,
                    }
                },
            }
        }
        
        movie_json = {
            'ContainerSettings': {
                'Container': 'MOV',
                'MovSettings': {}
            },
            'VideoDescription': {
                'CodecSettings': {
                    'Codec': 'H_264',
                    'H264Settings': {
                        'MaxBitrate': 1000000,
                        'RateControlMode': 'QVBR'
                    }
                }
            },
            'AudioDescriptions': [
                {
                    'AudioSourceName': 'Audio Selector 1',
                    'CodecSettings': {
                        'Codec': 'AAC',
                        'AacSettings': {
                            'SampleRate': 48000,
                            'CodingMode': 'CODING_MODE_2_0',
                        }
                    }
                }
            ]
        }
        
        response = client.create_job(
            Role=f"arn:aws:iam::{account_id}:role/{role_name}",
            JobTemplate=job_template,
            Settings={
                'Inputs': [
                    {
                        'FileInput': f"s3://{bucket_name}/input/{file_name}",
                        'AudioSelectors': {
                            'Audio Selector 1': {
                                'DefaultSelection': 'DEFAULT'
                            }
                        },
                        'VideoSelector': {},
                        'TimecodeSource': 'ZEROBASED'
                    }
                ],
                'OutputGroups': [
                    {
                        'Name': 'File Group',
                        'OutputGroupSettings': {
                            'Type': 'FILE_GROUP_SETTINGS',
                            'FileGroupSettings': {
                                'Destination': f"s3://{bucket_name}/output/"
                            }
                        },
                        'Outputs': [thumnail_json, movie_json]
                    }
                ]
            }
        )
        logging.info(response)
    except Exception as e:
        print(f"An error occurred: {e}")



    job_id = response['Job']['Id']
    logging.info(f"Job {job_id} created")

    return job_id


print("hoge")
# 上記の関数を呼び出してマウント操作を実行
if __name__ == '__main__':
    # set log
    logger = logging.getLogger(__name__)
    fmt = "%(asctime)s %(levelname)s %(name)s :%(message)s"
    logging.basicConfig(level=logging.INFO, format=fmt)

    # 環境変数のチェック
    logging.info("check environment")
    BUCKET_NAME = os.environ.get("BUCKET_NAME")
    MEDIA_CONVERT_JOB_TEMPLATE = os.environ.get("MEDIA_CONVERT_JOB_TEMPLATE")
    MEDIA_CONVERT_JOB_ROLE = os.environ.get("MEDIA_CONVERT_JOB_ROLE")
    
    missing_vars = []
    
    if BUCKET_NAME is None:
        missing_vars.append("BUCKET_NAME")
    
    if MEDIA_CONVERT_JOB_TEMPLATE is None:
        missing_vars.append("MEDIA_CONVERT_JOB_TEMPLATE")
    
    if MEDIA_CONVERT_JOB_ROLE is None:
        missing_vars.append("MEDIA_CONVERT_JOB_ROLE")
    
    if missing_vars:
        raise EnvironmentError(f"必要な環境変数が設定されていません: {', '.join(missing_vars)}")

    # list_bucket_contents(BUCKET_NAME)

    logging.info("mount s3")
    mount_point = '/app/hoge'  # マウント先ディレクトリ
    mount_s3(BUCKET_NAME, mount_point)
    
    # 動画ファイルのパス
    logging.info("get video duration")
    # file_name="video.mp4"
    file_name="countdown_1min.mp4"
    # file_name="countdown_10s.mp4"
    file_path = f"{mount_point}/input/{file_name}"
    video_duration = get_video_duration(file_path)
    
    if video_duration is not None:
        print(f'Video Duration: {video_duration} seconds')
    else:
        print('Failed to retrieve video duration')

    logging.info("create media job")
    job_id = create_media_convert_job(file_name, MEDIA_CONVERT_JOB_TEMPLATE, MEDIA_CONVERT_JOB_ROLE, BUCKET_NAME, video_duration)
    
    logging.info("complete")
