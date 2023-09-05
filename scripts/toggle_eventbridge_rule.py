import boto3
import os

def toggle_rule(rule_name):
    """EventBridgeルールの状態を切り替える関数"""
    client = boto3.client('events')
    
    try:
        # 現在のルールの状態を取得
        response = client.describe_rule(
            Name=rule_name
        )
        state = response['State']
        
        if state == 'ENABLED':
            # ルールを無効化
            client.disable_rule(
                Name=rule_name
            )
            print(f"Successfully disabled rule: {rule_name}")
        else:
            # ルールを有効化
            client.enable_rule(
                Name=rule_name
            )
            print(f"Successfully enabled rule: {rule_name}")
    except Exception as e:
        print(f"Failed to toggle rule: {rule_name}. Error: {e}")

if __name__ == "__main__":
    # 環境変数からルール名を取得
    rule_name = os.environ.get("EVENT_BRIDGE_RULE_NAME")
    
    if rule_name:
        # ルールの状態を切り替え
        toggle_rule(rule_name)
    else:
        print("Environment variable EVENT_BRIDGE_RULE_NAME is not set.")
