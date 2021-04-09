#!/usr/bin/env python3
# encoding: utf-8
# @author : hujincheng
# @time : 2021/4/9 17:02


from django.conf import settings
from django.core.files.storage import Storage

class MyStorage(Storage):

    def __init__(self, fdfs_base_url=None):
        # if not fdfs_base_url:
        #     self.fdfs_base_url = settings.FDFS_BASE_URL
        # self.fdfs_base_url = fdfs_base_url
        #
        self.fdfs_base_url = fdfs_base_url or settings.FDFS_BASE_URL


    def _open(self, name, mode ='rb'):
        pass


    def _save(self, name, content):
        pass


    def url(self, name):

        return self.fdfs_base_url+ name