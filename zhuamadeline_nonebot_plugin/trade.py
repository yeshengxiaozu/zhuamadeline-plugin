﻿from nonebot.adapters.onebot.v11 import MessageSegment, Message
from nonebot.adapters.onebot.v11 import GROUP, Bot, Event
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.log import logger
from nonebot import on_command, on_fullmatch
from nonebot.params import CommandArg
#加载文件操作系统
import json
#加载读取系统时间相关
import datetime
#加载数学算法相关
import random
import time
#加载madeline档案信息
from .madelinejd import *
from .config import *
from .list1 import *
from .list2 import *
from .list3 import *
#加载商店信息和商店交互
from .collection import collections
from .function import *
from .event import *
from .pvp import *
from .whitelist import whitelist_rule

user_path = Path() / "Data" / "UserList"
file_name = "UserData.json"
full_path = user_path / file_name
user_path1 = Path() / "data" / "UserList" / "UserList1.json"
user_path2 = Path() / "data" / "UserList" / "UserList2.json"
user_path3 = Path() / "data" / "UserList" / "UserList3.json"
user_path4 = Path() / "data" / "UserList" / "UserList4.json"

#确定一些事件
confirm = on_fullmatch(['.confirm', '。confirm'], permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@confirm.handle()
async def confirm_handle(bot: Bot, event: GroupMessageEvent):
    # 打开文件
    data = open_data(full_path)
    user_id = event.get_user_id()

    #判断是否开辟event事件栏
    if(not 'event' in data[str(user_id)]):
        data[str(user_id)]['event'] = 'nothing'

    if data[str(user_id)]['event'] == 'nothing':
        await confirm.finish("你现在似乎没有需要确定的事情", at_sender=True)

    elif data[str(user_id)]['event'] == 'trading':
        kind = data[str(user_id)]['trade']['物品'][0] # -1为藏品，其他是猎场
        good = data[str(user_id)]['trade']['物品'][1]
        amount = data[str(user_id)]['trade']['数量']
        price = data[str(user_id)]['trade']['单价']

        #对于高等级猎场madeline的交易判断
        #出新猎场要改
        madeline_dict = {
            1: (user_path1, madeline_data1),
            2: (user_path2, madeline_data2),
            3: (user_path3, madeline_data3),
            4: (user_path4, madeline_data4),
        }
        
        kind = int(kind)
        if kind in madeline_dict:
            madeline_path, chaxun = madeline_dict[kind]
        else:
            raise KeyError("不存在该猎场！")
            
        data2 = open_data(madeline_path)
        keepNum = data2[str(user_id)][good] #你目前拥有的该madeline数量
        k = good.split('_')
        level = int(k[0]) #抽取的madeline等级
        num = k[1] #抽取的madeline的ID
        name = chaxun.get(str(level)).get(num).get('name') #获取该madeline的名称
        if keepNum >= amount:
            data2[str(user_id)][good] -= amount
            #这应该不会发生吧...但我还是加上了这个判断
            if(not 'berry' in data[str(user_id)]):
                data[str(user_id)]['berry'] = 1000
            berry = amount * price
            data[user_id]['berry'] += berry
            data[str(user_id)]['event'] = 'nothing'
            #写入主数据表
            save_data(full_path, data)
            save_data(madeline_path, data2)
            await confirm.finish(f"交易成功！你获得了{berry}草莓。\n商人很喜欢与你的这一次交易，他期待着下次与你见面", at_sender=True)
        else:
            await confirm.finish(f"你没有足够多的{name}，你需要{amount}个，但你目前只拥有{keepNum}个", at_sender=True)
            
#取消一些事件
deny = on_fullmatch(['.deny', '。deny'], permission=GROUP, priority=1, block=True, rule=whitelist_rule)
@deny.handle()
async def deny_handle(bot: Bot, event: GroupMessageEvent):
    # 打开文件
    data = open_data(full_path)
    user_id = event.get_user_id()
    if (str(user_id) in data):
        # 添加全局冷却
        group_id = str(event.group_id)
        all_cool_time(cd_path, user_id, group_id)
    #判断是否开辟event事件栏
    if(not 'event' in data[str(user_id)]):
        data[str(user_id)]['event'] = 'nothing'

    if data[str(user_id)]['event'] == 'nothing':
        await confirm.finish("你现在似乎没有需要确定的事情", at_sender=True)
    elif data[str(user_id)]['event'] == 'trading':
        data[str(user_id)]['event'] = 'nothing'
        #写入主数据表
        save_data(full_path, data)
        await deny.finish("商人失望地离开了...", at_sender=True)