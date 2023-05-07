# Description: 腾讯云短信发送接口封装   
import json
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.sms.v20210111 import sms_client, models

import Globals
class TencentSmsSender:
    def __init__(self, region="ap-beijing"):
        secret_id=Globals.SMS_SECRETID
        secret_key=Globals.SMS_SECRETKEY
        self.cred = credential.Credential(secret_id, secret_key)
        http_profile = HttpProfile()
        http_profile.endpoint = "sms.tencentcloudapi.com"
        client_profile = ClientProfile()
        client_profile.httpProfile = http_profile
        self.client = sms_client.SmsClient(self.cred, region, client_profile)

    def send_sms(self, phone_number:int, template_param_set: list[str]):
        req = models.SendSmsRequest()
        sms_sdk_app_id="1400816394"
        sign_name="小慧很智慧"
        template_id="1788091"
        
        params = {
            "PhoneNumberSet": [phone_number],
            "SmsSdkAppId": sms_sdk_app_id,
            "SignName": sign_name,
            "TemplateId": template_id,
            "TemplateParamSet": template_param_set
        }
        req.from_json_string(json.dumps(params))

        try:
            resp = self.client.SendSms(req)
            return resp.to_json_string()
        except TencentCloudSDKException as err:
            return str(err)

# 使用方法：
# 1. 创建一个TencentSmsSender实例
# sms_sender = TencentSmsSender("Your_SecretId", "Your_SecretKey")

# 2. 调用send_sms方法发送短信
# response = sms_sender.send_sms("15079857414", "1400816394", "小慧很智慧", "1788091", ["1234"])
# print(response)

if __name__ == "__main__":
    sms_sender = TencentSmsSender("Your_SecretId", "Your_SecretKey")
