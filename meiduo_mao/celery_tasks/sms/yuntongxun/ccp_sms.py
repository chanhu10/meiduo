from ronglian_sms_sdk import SmsSDK
import json

accId = '8aaf0708780055cd0178294f52990f7e'
accToken = 'd23abddebf0342f6ae87c40f1ff3f88c'
appId = '8aaf0708780055cd017829532a650f87'

#
# def send_message():
#     sdk = SmsSDK(accId, accToken, appId)
#     tid = '1'
#     mobile = '15558029150'
#     datas = ('666888', '2')
#     resp = sdk.sendMessage(tid, mobile, datas)
#     print(resp)

class CCP(object):

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = super(CCP, cls).__new__(cls, *args, **kwargs)
            cls._instance.sdk = SmsSDK(accId, accToken, appId)

        return cls._instance

    def send_message(self, tid, mobile, datas):
        # tid = '1'
        # mobile = '15558029150'
        # datas = ('666888', '2')
        resp = self.sdk.sendMessage(tid, mobile, datas)
        resp = json.loads(resp)
        if resp.get('statusCode') == "000000":
            return 0
        else:
            return -1



if __name__ == '__main__':

    CCP().send_message(tid='1', mobile = '15558029150', datas = ('666888', '2'))

