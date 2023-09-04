from constructs import Construct
from aws_cdk import (
    Duration,
    Stack,
    RemovalPolicy,
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_events as events,
    aws_events_targets as targets,
    aws_s3 as s3,
    aws_iam as iam,
    aws_ecr as ecr,
    aws_ecr_assets as ecr_assets,
    aws_ecs_patterns as ecs_patterns,
    aws_applicationautoscaling as appscaling,
    aws_logs as logs,
    aws_mediaconvert as mediaconvert,
)


class CdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # VPCの作成
        vpc = ec2.Vpc(self, "MyVpc", max_azs=2)

        # ECSクラスタの作成
        cluster = ecs.Cluster(self, "Ec2Cluster", vpc=vpc)

        # EC2 キャパシティをクラスタに追加
        cluster.add_capacity("MyExtraCapacityGroup",
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.MICRO),
            desired_capacity=1
        )

        # DockerイメージをECRにプッシュ
        docker_image = ecr_assets.DockerImageAsset(self, "DockerAsset",
            directory="./docker/"  # Dockerfileが置かれているディレクトリへのパス
        )

        # S3バケットの作成
        bucket = s3.Bucket(self, "MyBucket", removal_policy=RemovalPolicy.DESTROY)
        
        # CloudWatch Logs グループの作成
        log_group = logs.LogGroup(self, "LogGroup",
            removal_policy=RemovalPolicy.DESTROY  # スタック削除時にロググループも削除
        )

        # EC2タスク定義の作成
        task_definition = ecs.Ec2TaskDefinition(self, "TaskDef")
        
        # コンテナを特権モードで追加
        task_definition.add_container("AppContainer",
            image=ecs.ContainerImage.from_docker_image_asset(docker_image),
            memory_limit_mib=512,
            environment={
                'BUCKET_NAME': bucket.bucket_name  # 環境変数にS3バケット名を設定
            },
            logging=ecs.LogDriver.aws_logs(
                stream_prefix="ScheduledEc2Task",
                log_group=log_group,
            ),
            privileged=True,  # 特権モードを有効にする
        )

        # S3のAdmin権限をタスクロールに割り当てる
        task_definition.task_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess")
        )
        task_definition.task_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AWSElementalMediaConvertFullAccess")
        )

        # スケジュールに基づいてECSタスクを実行
        scheduled_ecs_task = ecs_patterns.ScheduledEc2Task(self, "ScheduledEc2Task",
            cluster=cluster,  # ECSクラスタ
            scheduled_ec2_task_definition_options=ecs_patterns.ScheduledEc2TaskDefinitionOptions(
                task_definition=task_definition  # 作成したタスク定義を指定
            ),
            schedule=appscaling.Schedule.rate(Duration.minutes(5)),  # 5分ごとに実行
            desired_task_count=1  # 実行するタスクの数
        )


        # MediaConvert用
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
                        'FramerateNumerator': 1,
                        'FramerateDenominator': 2,
                        'MaxCaptures': 11,
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

        # Create a MediaConvert Job Template
        mediaconvert.CfnJobTemplate(
            self, 'MediaConvertJobTemplate',
            name='MyJobTemplate',
            description='Job template to create thumbnails',
            settings_json={
                'OutputGroups': [
                    {
                        'Name': 'File Group',
                        'OutputGroupSettings': {
                            'Type': 'FILE_GROUP_SETTINGS',
                            'FileGroupSettings': {}
                        },
                        'Outputs': [thumnail_json, movie_json]
                    }
                ]
            }
        )
