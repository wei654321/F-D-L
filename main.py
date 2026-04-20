import os
import requests
import time
import json
import fgourl
import user
import coloredlogs
import logging
import sys

# 配置日志
logger = logging.getLogger("FGO Daily Login")
coloredlogs.install(fmt='%(asctime)s %(name)s %(levelname)s %(message)s')

# 获取环境变量
try:
    userIds = os.environ['userIds'].split(',')
    authKeys = os.environ['authKeys'].split(',')
    secretKeys = os.environ['secretKeys'].split(',')
    
    # 检查数组长度是否一致
    if not (len(userIds) == len(authKeys) == len(secretKeys)):
        logger.error("环境变量长度不匹配！请确保userIds, authKeys, secretKeys数量相同")
        sys.exit(1)
        
except KeyError as e:
    logger.error(f"缺少必要的环境变量: {e}")
    logger.info("请在GitHub Actions Secrets中设置以下变量:")
    logger.info("1. userIds: 用户ID，多个用逗号分隔")
    logger.info("2. authKeys: 认证密钥，多个用逗号分隔")
    logger.info("3. secretKeys: 密钥，多个用逗号分隔")
    sys.exit(1)

# 可选环境变量
webhook_discord_url = os.environ.get('webhookDiscord', '')
device_info = os.environ.get('DEVICE_INFO_SECRET', '')
appCheck = os.environ.get('APP_CHECK_SECRET', '')
user_agent_2 = os.environ.get('USER_AGENT_SECRET_2', '')

# 地区设置
fate_region = os.environ.get('FATE_REGION', 'JP')  # 默认为JP
logger.info(f"使用地区: {fate_region}")

userNums = len(userIds)
authKeyNums = len(authKeys)
secretKeyNums = len(secretKeys)

logger.info(f"找到 {userNums} 个用户账号")

def get_latest_verCode():
    """获取最新的版本代码"""
    endpoint = "https://raw.githubusercontent.com/DNNDHH/FGO-VerCode-extractor/JP/VerCode.json"
    
    try:
        response = requests.get(endpoint, timeout=10)
        response.raise_for_status()
        response_data = json.loads(response.text)
        ver_code = response_data.get('verCode', '')
        logger.info(f"获取到版本代码: {ver_code}")
        return ver_code
    except Exception as e:
        logger.error(f"获取版本代码失败: {e}")
        return ''

def get_latest_appver():
    """获取最新的应用版本"""
    endpoint = "https://raw.githubusercontent.com/DNNDHH/FGO-VerCode-extractor/JP/VerCode.json"
    
    try:
        response = requests.get(endpoint, timeout=10)
        response.raise_for_status()
        response_data = json.loads(response.text)
        app_ver = response_data.get('appVer', '')
        logger.info(f"获取到应用版本: {app_ver}")
        return app_ver
    except Exception as e:
        logger.error(f"获取应用版本失败: {e}")
        return '2.100.100'  # 返回一个默认版本

def main():
    logger.info("=" * 50)
    logger.info("FGO每日登录脚本启动")
    logger.info("=" * 50)
    
    # 检查用户数量是否匹配
    if not (userNums == authKeyNums == secretKeyNums):
        logger.error(f"账号信息数量不匹配！用户: {userNums}, 认证: {authKeyNums}, 密钥: {secretKeyNums}")
        sys.exit(1)
    
    # 设置最新的游戏资源
    logger.info("正在获取最新的游戏资源...")
    try:
        fgourl.set_latest_assets()
        logger.info("资源获取成功")
    except Exception as e:
        logger.error(f"获取游戏资源失败: {e}")
        logger.warning("将继续尝试登录，但可能遇到版本不兼容问题")
    
    # 遍历所有用户
    for i in range(userNums):
        user_id = userIds[i].strip()
        auth_key = authKeys[i].strip()
        secret_key = secretKeys[i].strip()
        
        logger.info("=" * 50)
        logger.info(f"[{i+1}/{userNums}] 处理用户: {user_id[:5]}...")
        logger.info("=" * 50)
        
        try:
            # 创建用户实例
            instance = user.user(user_id, auth_key, secret_key)
            
            # 执行登录流程
            time.sleep(1)
            instance.topLogin()
            
            time.sleep(2)
            instance.topHome()
            
            time.sleep(0.5)
            instance.lq001()
            
            time.sleep(0.5)
            instance.Present()
            
            time.sleep(0.5)
            instance.lq002()
            
            time.sleep(2)
            instance.buyBlueApple()
            
            time.sleep(1)
            instance.lq003()
            
            time.sleep(1)
            
            # 检查是否运行免费扭蛋
            if "--Free_Gacha" in sys.argv:
                logger.info("执行免费扭蛋...")
                instance.Free_Gacha()
                time.sleep(2)
            
            # 执行友情点召唤
            instance.drawFP()
            time.sleep(1)
            
            # 可选的额外功能
            # instance.LTO_Gacha()
            # instance.LTO_drawFP()
            
            logger.info(f"用户 {user_id[:5]}... 登录流程完成")
            
        except Exception as ex:
            logger.error(f"处理用户 {user_id[:5]}... 时出错: {ex}")
            # 继续处理下一个用户
        
        # 用户间延时
        if i < userNums - 1:
            logger.info(f"等待5秒后处理下一个用户...")
            time.sleep(5)
    
    logger.info("=" * 50)
    logger.info("所有用户处理完成")
    logger.info("=" * 50)
    
    # 发送Discord通知（如果配置了webhook）
    if webhook_discord_url:
        try:
            send_discord_notification()
        except Exception as e:
            logger.error(f"发送Discord通知失败: {e}")

def send_discord_notification():
    """发送Discord通知"""
    if not webhook_discord_url:
        return
    
    payload = {
        "content": f"✅ FGO自动登录完成 - {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "embeds": [{
            "title": "登录结果",
            "description": f"成功处理 {userNums} 个账号",
            "color": 3066993,  # 绿色
            "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        }]
    }
    
    try:
        response = requests.post(webhook_discord_url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("Discord通知发送成功")
    except Exception as e:
        logger.error(f"发送Discord通知失败: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("用户中断执行")
    except Exception as e:
        logger.error(f"脚本执行失败: {e}")
        sys.exit(1)
