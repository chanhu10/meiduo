# 定义任务
from celery_tasks.sms.yuntongxun.ccp_sms import CCP
from celery_tasks.main import celery_app

# 使用装饰器装饰异步事务，保证celery识别任务
@celery_app.task()
def send_sms_code(mobile, sms_code):
    """
    发送短信验证码的异步任务
    :param mobile: 手机号
    :param sms_code:短信验证码
    :return:成功：0 失败：-1
    """

    send_res = CCP().send_message(tid="1", mobile=mobile, datas=(sms_code, "5"))

    return send_res