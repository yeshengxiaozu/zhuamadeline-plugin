import datetime
import json
import random
import math
from pathlib import Path
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot import get_bot
from .list1 import *
from .list2 import *
from .list3 import *
from .list4 import *
from .function import open_data, save_data, print_zhua, time_decode, buff2_change_status
from .config import ban, bot_owner_id, connect_bot_id
from .whitelist import whitelist_rule
from .shop import item
from .pvp import check_liechang
#事件系统
#在道具使用和普通的抓madeline中会触发

user_path = Path() / "data" / "UserList" / "UserData.json"
user_list1 = Path() / "data" / "UserList" / "UserList1.json"
user_list2 = Path() / "data" / "UserList" / "UserList2.json"
user_list3 = Path() / "data" / "UserList" / "UserList3.json"
user_list4 = Path() / "data" / "UserList" / "UserList4.json"
stuck_path = Path() / "data" / "UserList" / "Struct.json"
bar_path = Path() / "data" / "UserList" / "bar.json"

#脱险事件
async def outofdanger(data, user_id, message, current_time, next_time_r):
    stuck_data = open_data(stuck_path)  # 打开被困名单
    user_info = data.setdefault(str(user_id), {})
    liechang_number = user_info.get('lc','1')
    buff = user_info.get("buff", "normal")
    
    # 检测是否在名单中
    if user_id in stuck_data:
        # 处理buff2状态逻辑
        data = buff2_change_status(data, user_id, "lucky", 1)
        data = buff2_change_status(data, user_id, "speed", 1)
        # 是否到时间了
        if current_time >= next_time_r:
            user_info["buff"] = "normal"
            del stuck_data[user_id]
            save_data(user_path, data)
            save_data(stuck_path, stuck_data)
            await message.finish("恭喜你成功脱险....", at_sender=True)
        else:
            save_data(user_path, data)
            await message.finish("你还处在危险之中...", at_sender=True)
        return
    # 有buff也解除
    if buff in ["hurt", "lost", "confuse"]:
        # 处理buff2状态逻辑
        data = buff2_change_status(data, user_id, "lucky", 1)
        data = buff2_change_status(data, user_id, "speed", 1)
        # 其他逻辑
        user_info["buff"] = "normal"
        user_info["next_time"] = current_time.strftime("%Y-%m-%d %H:%M:%S")
        save_data(user_path, data)
        msg = "恭喜你成功脱险...." if buff in ["hurt", "lost"] else "看了半天你还是没想明白这是什么东西，但你意识到不能再在原地停留了"
        await message.finish(msg, at_sender=True)
    
    # 没到时间加1幸运
    if current_time <= next_time_r:
        # 处理buff2状态逻辑
        data = buff2_change_status(data, user_id, "lucky", 1)
        data = buff2_change_status(data, user_id, "speed", 1)
        return

    # 0猎加1幸运
    if liechang_number == "0":
        # 处理buff2状态逻辑
        data = buff2_change_status(data, user_id, "lucky", 1)
        data = buff2_change_status(data, user_id, "speed", 1)
        return


async def event_happen(user_data, user_id, message, diamond_text, hourglass_text):
    # 设定默认值
    user_info = user_data.setdefault(user_id, {})
    # 读取猎场编号
    liechang_number = user_info.get('lc', '1')

    # 猎场函数映射
    liechang_functions = {
        '1': PlainStuck,
        '2': ForestStuck,
        '3': CrystalStuck,
        '4': LabStuck,
        '5': AbyssStuck,
    }
    # 获取对应的函数
    event_function = liechang_functions.get(liechang_number)
    if event_function is None:  # 如果猎场编号无效
        raise ValueError("错误的猎场编号")
    # 调用对应的函数
    await event_function(user_data, user_id, message, diamond_text, hourglass_text)

# 一猎事件
async def PlainStuck(user_data, user_id, message, diamond_text, hourglass_text):
    # 初始化默认值
    user_id = str(user_id)
    user_info = user_data.setdefault(user_id, {})
    user_info.setdefault('berry', 0)
    items = user_info.setdefault('item', {})
    collections = user_info.setdefault('collections', {})
    user_info.setdefault('event', 'nothing')
    user_info.setdefault('trade', {})
    user_info.setdefault('buff2', 'normal')
    liechang_number = user_info.get('lc', '1')
    current_time = datetime.datetime.now()
    
    # 获取调律器
    rnd_regu = 20 if collections.get("调律器", 0) >= 1 else 0
    
    rnd = random.randint(1, 1000)
    # 遇到金矿
    if rnd <= 20 + rnd_regu:
        berry = random.randint(100, 200)
        user_info['berry'] += berry
        save_data(user_path, user_data)
        await message.finish(f"呀，你在庇护所外面的草丛里发现了一片草莓丛，你摘了{berry}颗草莓！"+ diamond_text+hourglass_text, at_sender=True)

    # 获得神秘碎片
    elif rnd <= 40 + rnd_regu and items.get('神秘碎片', 0) < 5:
        next_time = current_time + datetime.timedelta(minutes=59 if collections.get("回想之核", 0) >= 1 else 60)
        #检测星钻
        if diamond_text:
            next_time = current_time  # 立即重置冷却时间
 
        user_info['next_time'] = next_time.strftime("%Y-%m-%d %H:%M:%S")
        items['神秘碎片'] = items.get('神秘碎片', 0) + 1
        save_data(user_path, user_data)
        await message.finish("你在一个人迹罕至的地方捡到了一个泛着蓝光的神秘碎片，出于好奇和困惑你在此观察了一个小时"+ diamond_text+hourglass_text, at_sender=True)

    # 获得幸运药水
    elif rnd <= 50 + rnd_regu:
        items['幸运药水'] = items.get('幸运药水', 0) + 1
        save_data(user_path, user_data)
        await message.finish("你捡到了一瓶奇怪的药水，似乎是别人遗留下来的？"+ diamond_text+hourglass_text, at_sender=True)

    # 获得木质十字架
    elif rnd <= 60 + rnd_regu and '木质十字架' not in collections:
        collections['木质十字架'] = 1
        save_data(user_path, user_data)
        await message.finish("这是？？？\n输入.cp 木质十字架 以查看具体效果"+ diamond_text+hourglass_text, at_sender=True)

    # 获得天使之羽
    elif rnd <= 70 + rnd_regu and '天使之羽' not in collections:
        collections['天使之羽'] = 1
        save_data(user_path, user_data)
        await message.finish("一片散发着柔和光芒的羽毛缓缓飘落在你的手中，羽毛上似乎蕴含着某种神秘的力量。\n输入.cp 天使之羽 以查看具体效果"+ diamond_text+hourglass_text, at_sender=True)

    # 遇到流浪商人
    elif rnd <= 110 + rnd_regu:
        data1 = open_data(user_list1)
        if user_id not in data1:
            return
        user_info.setdefault("event", "nothing")
        user_info.setdefault("trade", {})
            
        # 处理buff2状态逻辑
        
        user_data = buff2_change_status(user_data, user_id, "lucky", 1)
        user_data = buff2_change_status(user_data, user_id, "speed", 1)
        user_info = user_data.get(user_id,{})
        
        user_info['event'] = 'trading'

        k1 = random.choice(list(data1[user_id].keys()))
        k = k1.split('_')
        level = int(k[0])
        num = k[1]
        if [level, int(num)] in rabbit_madeline1:
            priceRate = 0.8
        else:
            priceRate = 1
        name = madeline_data1.get(str(level)).get(num).get('name')
        if level == 1:
            price = random.randint(5, 20)
            amount = random.randint(1, 5)
        elif level == 2:
            price = random.randint(8, 25)
            amount = random.randint(1, 4)
        elif level == 3:
            price = random.randint(15, 40)
            amount = random.randint(1, 3)
        elif level == 4:
            price = random.randint(40, 120)
            amount = random.randint(1, 2)
        elif level == 5:
            price = random.randint(120, 240)
            amount = 1
        else:
            raise KeyError("Invalid level number")
        price = math.floor(price * priceRate)

        user_info['trade']['数量'] = amount
        user_info['trade']['单价'] = price
        user_info['trade']['物品'] = [int(liechang_number), k1]
        user_info['event'] = 'trading'
        next_time = current_time
        user_info['next_time'] = next_time.strftime("%Y-%m-%d %H:%M:%S")
        save_data(user_path, user_data)
        await message.finish(
            f"你遇到了一位流浪商人，他似乎想从你这里买点东西\n"
            f"“你好啊，我在收集一些madeline。现在我需要{amount}个{name}”，我听说这好像是个{level}级的madeline，所以我愿意以每个madeline {price}草莓的价格收购，不知你是否愿意。”\n"
            "只有拥有足够的该madeline才可确定交易，并且只能一次性卖完，不支持分批出售\n"
            "输入.confirm 确定出售，输入.deny 拒绝本次交易", at_sender=True)
    else:
        return
            
    
# 二号猎场事件
async def ForestStuck(user_data, user_id, message, diamond_text, hourglass_text):
    # 初始化默认值
    user_id = str(user_id)
    user_info = user_data.setdefault(user_id, {})
    user_info.setdefault('berry', 0)
    collections = user_info.setdefault("collections", {})
    items = user_info.setdefault("item", {})
    user_info.setdefault('debuff', "normal")
    user_info.setdefault("buff2", "normal")
    user_info.setdefault("event", "nothing")
    user_info.setdefault("trade", {})
    liechang_number = user_info.get('lc', '1')
    current_time = datetime.datetime.now()
    
    # 获取调律器
    rnd_regu = 20 if collections.get("调律器", 0) >= 1 else 0

    # 打开被困名单
    stuck_data = open_data(stuck_path)

    # 判断是否迷路（默认迷路）
    lost = 0 if items.get("指南针", 0) >= 1 else 1

    # 迷路事件
    if lost == 1:
        rnd = random.randint(1, 10)
        if rnd <= 2:
            return
        else:
            next_time = current_time + datetime.timedelta(minutes=479 if collections.get("回想之核", 0) >= 1 else 480)
            user_info['next_time'] = next_time.strftime("%Y-%m-%d %H:%M:%S")
            user_info['buff'] = 'lost'
            # 加入森林被困名单
            stuck_data[user_id] = '2'
            # 处理buff2状态逻辑
            user_data = buff2_change_status(user_data, user_id, "lucky", 1)
            user_data = buff2_change_status(user_data, user_id, "speed", 1)
            # 写入数据
            save_data(user_path, user_data)
            save_data(stuck_path, stuck_data)
            # 发送消息
            await message.finish("你在森林里迷路了，不知道何时才能走出去……(请在你觉得可能找到路的时候使用zhuamadeline指令)"+diamond_text+hourglass_text, at_sender=True)

    ###### 其他事件 #####
    rnd = random.randint(1, 1000)
    # 遇到金矿
    if rnd <= 25 + rnd_regu:
        berry = random.randint(150, 250)
        user_info['berry'] += berry
        save_data(user_path, user_data)
        await message.finish(f"呀，你在森林里发现了一颗变异的草莓树（为什么会有草莓树？），你摘下了{berry}颗草莓！"+ diamond_text+hourglass_text, at_sender=True)

    # 遇到被困人员
    elif rnd <= 150 + rnd_regu:
        if len(stuck_data) >= 1:
            save_id = random.choice(list(stuck_data.keys()))
            if stuck_data[save_id] != '2':
                return
            user_info['berry'] += 75
            # 确保被救者也存在于主数据中
            rescue_user = user_data.setdefault(save_id, {})
            rescue_user['next_time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            del stuck_data[save_id]
            save_data(user_path, user_data)
            save_data(stuck_path, stuck_data)
            await message.finish(f"恭喜你救出了森林里的" + MessageSegment.at(save_id) + "。\n本次奖励75草莓"+ diamond_text+hourglass_text, at_sender=True)
        else:
            return

    # 受伤事件
    elif rnd <= 250 + rnd_regu:
        #有迅捷正常抓
        if user_info['buff2'] == 'speed':
            return
        # 处理buff2状态逻辑
        user_data = buff2_change_status(user_data, user_id, "lucky", 1)
        next_time = current_time + datetime.timedelta(minutes=59 if collections.get("回想之核", 0) >= 1 else 60)
        user_info['buff'] = 'hurt'
        stuck_data[user_id] = '2'
            
        #检测星钻
        if diamond_text:
            next_time = current_time  # 立即重置冷却时间
            del stuck_data[user_id]
            user_info['buff'] = 'normal'
        user_info['next_time'] = next_time.strftime("%Y-%m-%d %H:%M:%S")
        
        save_data(user_path, user_data)
        save_data(stuck_path, stuck_data)
        text = [
            "你被路边的荆棘刺到了！",
            "抓madeline的途中，你掉进了莫名奇妙塌陷的大坑里，",
            "走着走着，树上的金草莓落下来砸到你身上，爆炸了，把你炸伤了！",
            "你走进一个山洞，可此地暗得你完全找不着北，你一不小心就被山洞里的石头刮伤了！"
        ]
        await message.finish(random.choice(text) + "你需要原地等待一个小时，或者使用急救包自救，又或者等待他人来救你……"+diamond_text+hourglass_text, at_sender=True)

    # 神秘碎片事件
    elif rnd <= 270 + rnd_regu:
        # 确保道具栏存在（已提前setdefault items）
        if items.get('神秘碎片', 0) < 5:
            next_time = current_time + datetime.timedelta(minutes=59 if collections.get("回想之核", 0) >= 1 else 60)
            user_info['buff'] = 'confuse'
            items['神秘碎片'] = items.get('神秘碎片', 0) + 1
            stuck_data[user_id] = '2'
            #检测星钻
            if diamond_text:
                next_time = current_time  # 立即重置冷却时间
                del stuck_data[user_id]
                user_info['buff'] = 'normal'
            user_info['next_time'] = next_time.strftime("%Y-%m-%d %H:%M:%S")
            save_data(user_path, user_data)
            save_data(stuck_path, stuck_data)
            await message.finish("你捡到了一个泛着蓝光的神秘碎片，出于好奇和困惑你在此观察了一个小时\n或许有人发现你的时候...你才会停止观察"+diamond_text+hourglass_text, at_sender=True)
        else:
            return

    # 生命之叶事件
    elif rnd <= 275 + rnd_regu:
        if "生命之叶" not in collections:
            collections["生命之叶"] = 1
            save_data(user_path, user_data)
            await message.finish(
                "你在神秘森林中跋涉，寒冷的湿气缠绕在你周围，树影在雾中飘动。突然，一缕微光在脚下闪烁，几乎让人错以为是错觉。你蹲下去，拨开层层枯叶与苔藓，手指触碰到一片散发着温暖绿色光芒的叶子。\n“生命之叶”\n它在你掌中微微颤动，似乎蕴藏着久违的生机。周围的迷雾在这一刻似乎变得稍微稀薄，你感到一丝久违的希望。此物似乎带有古老而神秘的力量——一种与你旅程息息相关的力量。\n输入.cp 生命之叶 以查看具体效果"+ diamond_text+hourglass_text,
                at_sender=True)
        else:
            return

    # 木质十字架事件
    elif rnd <= 285 + rnd_regu:
        if "木质十字架" not in collections:
            collections["木质十字架"] = 1
            save_data(user_path, user_data)
            await message.finish("这是？？？\n输入.cp 木质十字架 以查看具体效果"+ diamond_text+hourglass_text, at_sender=True)
        else:
            return

    # 调律器事件
    elif rnd <= 290 + rnd_regu:
        if "调律器" not in collections:
            collections["调律器"] = 1
            save_data(user_path, user_data)
            await message.finish("你感到一阵微妙的波动，似乎空气中有某种力量在流动。一件金属质感的仪器悄然出现在你手中，散发出微弱的光辉。\n输入.cp 调律器 以查看具体效果"+ diamond_text+hourglass_text, at_sender=True)
        else:
            return

    # 回想之核事件
    elif rnd <= 291 + rnd_regu:
        if "回想之核" not in collections:
            collections["回想之核"] = 1
            save_data(user_path, user_data)
            await message.finish("你在探索之时，突然一颗光辉璀璨的核心缓缓漂浮到你掌心。它散发着奇异的光芒，仿佛能带来超凡的力量。\n输入.cp 回想之核 以查看具体效果"+ diamond_text+hourglass_text, at_sender=True)
        else:
            return

    # 流浪商人事件
    elif rnd <= 341 + rnd_regu:
        data2 = open_data(user_list2)
        if user_id not in data2:
            return
        # 处理buff2状态逻辑
        user_data = buff2_change_status(user_data, user_id, "lucky", 1)
        user_data = buff2_change_status(user_data, user_id, "speed", 1)
        user_info = user_data.get(user_id,{})
        
        user_info['event'] = 'trading'

        k1 = random.choice(list(data2[user_id].keys()))
        k = k1.split('_')
        level = int(k[0])
        num = k[1]
        if [level, int(num)] in rabbit_madeline2:
            priceRate = 0.8
        else:
            priceRate = 1
        name = madeline_data2.get(str(level)).get(num).get('name')
        if level == 1:
            price = random.randint(7, 25)
            amount = random.randint(1, 5)
        elif level == 2:
            price = random.randint(10, 30)
            amount = random.randint(1, 4)
        elif level == 3:
            price = random.randint(20, 50)
            amount = random.randint(1, 3)
        elif level == 4:
            price = random.randint(50, 150)
            amount = random.randint(1, 2)
        elif level == 5:
            price = random.randint(150, 300)
            amount = 1
        else:
            raise KeyError("Invalid level number")

        price = math.floor(price * priceRate)

        user_info['trade']['数量'] = amount
        user_info['trade']['单价'] = price
        user_info['trade']['物品'] = [int(liechang_number), k1]
        user_info['event'] = 'trading'
        next_time = current_time
        user_info['next_time'] = next_time.strftime("%Y-%m-%d %H:%M:%S")
        save_data(user_path, user_data)
        await message.finish(
            f"你遇到了一位流浪商人，他似乎想从你这里买点东西\n"
            f"“你好啊，我在收集一些madeline。现在我需要{amount}个{name}”，我听说这好像是个{level}级的madeline，所以我愿意以每个madeline {price}草莓的价格收购，不知你是否愿意。”\n"
            "只有拥有足够的该madeline才可确定交易，并且只能一次性卖完，不支持分批出售\n"
            "输入.confirm 确定出售，输入.deny 拒绝本次交易", at_sender=True)
    else:
        return

#三号猎场事件
async def CrystalStuck(user_data, user_id, message, diamond_text, hourglass_text):
    # 初始化默认值
    user_id = str(user_id)
    user_info = user_data.setdefault(user_id, {})
    user_info.setdefault('berry', 0)
    collections = user_info.setdefault("collections", {})
    items = user_info.setdefault("item", {})
    user_info.setdefault('event', 'nothing')
    user_info.setdefault('trade', {})
    user_info.setdefault('buff2', 'normal')
    user_info.setdefault('debuff', "normal")
    liechang_number = user_info.get('lc', '1')
    current_time = datetime.datetime.now()
    
    # 获取调律器
    rnd_regu = 20 if collections.get("调律器", 0) >= 1 else 0
    
    bot = get_bot()
    
    #打开矿洞被困名单
    stuck_data = open_data(stuck_path)
    #是否拥有7个碎片
    if(items.get('神秘碎片',0) < 5):
        # 处理buff2状态逻辑
        user_data = buff2_change_status(user_data, user_id, "lucky", 1)
        user_data = buff2_change_status(user_data, user_id, "speed", 1)
        user_info = user_data.get(user_id,{})
        user_info['next_time'] = current_time.strftime("%Y-%m-%d %H:%M:%S")
        save_data(user_path, user_data)
        await message.finish("在远古的水晶矿洞前，风轻轻吹过，岩石间传来阵阵低语。眼前的巨大门扉上镶嵌着神秘的符文，发出幽幽的光辉。你注意到面前门上的部分符文与你手上的碎片相契合\n或许......收集足够的碎片就可以打开这扇门？", at_sender=True)
    
    #计算三个猎场的五级
    user_list = [user_list1, user_list2, user_list3]
    num_of_level5 = 0
    for file_path in user_list:
        data = open_data(file_path)
        if user_id in data:
            for k in data[user_id].keys():
                if int(k[0]) == 5:  # 直接判断级别
                    num_of_level5 += 1
    
    if num_of_level5 < 9:
        # 处理buff2状态逻辑
        user_data = buff2_change_status(user_data, user_id, "lucky", 1)
        user_data = buff2_change_status(user_data, user_id, "speed", 1)
        user_info = user_data.get(user_id,{})
        user_info['next_time'] = current_time.strftime("%Y-%m-%d %H:%M:%S")
        save_data(user_path, user_data)
        await message.finish(f"水晶矿洞内传来了强大的灵力，这股力量使你无法前进。或许......多带几个猎场的高等级madeline可以抵御这股力量？\n你目前有{num_of_level5}个5级madeline", at_sender=True)

    ######其他事件#####
    rnd = random.randint(1,1000)
    #抓到了特殊的道具
    if rnd <= 100:  # 10% 几率
        # debuff 检测逻辑
        debuff = user_info.setdefault('debuff', 'normal')
        if debuff == 'illusory':
            return
        
        rnd_tool = random.randint(1, 1000)
        
        # 开辟道具栏
        items.setdefault('草莓果酱', 0)
        items.setdefault('时间秒表', 0)
        items.setdefault('madeline提取器', 0)
        
        if rnd_tool < 20:
            # 检查 ban 列表
            mibao = ""
            if user_id in ban:
                if not '尘封的宝藏' in collections:
                    collections['尘封的宝藏'] = 1
                    mibao = "\n此外，在溶洞的一处昏暗角落，你意外发现了一件布满灰尘的秘宝。\n输入.cp 尘封的宝藏 以查看具体效果"
                
                items['madeline提取器'] += 1
                items['时间秒表'] += 1
                items['草莓果酱'] += 5

                save_data(user_path, user_data)
                await message.finish(
                    f"你误打误撞迷失了方向，来到一处隐秘的小溶洞。"
                    f"洞内一片寂静，昏暗中一张桌子上散落着几件道具："
                    f"草莓果酱×5、时间秒表×1、madeline提取器×1。" + mibao +diamond_text+hourglass_text,
                    at_sender=True
                )
            
            if not '鲜血之刃' in collections:
                collections['鲜血之刃'] = 1
                save_data(user_path, user_data)
                await message.finish(
                    "你误打误撞迷失了方向，来到一处隐秘的小溶洞。"
                    "洞内一片寂静，昏暗中你看到鲜血之刃静静地插在一块满是裂痕的石台上，"
                    "刀身被干涸的暗红血迹覆盖，仿佛在述说它的血腥过往。"
                    "洞内的空气冰冷刺骨，死寂中隐约传来低沉的嗡鸣，如同它在呼唤，渴求鲜血的滋养。\n"
                    "输入.cp 鲜血之刃 以查看具体效果"+ diamond_text+hourglass_text,
                    at_sender=True
                )
        
        # 其他奖励
        elif 51 <= rnd_tool <= 160:
            items['弹弓'] = items.get('弹弓', 0) + 1
            save_data(user_path, user_data)
            await message.finish("你发现了其他探险者在此遗落的一个弹弓"+diamond_text+hourglass_text, at_sender=True)
        
        elif 331 <= rnd_tool <= 500:
            items['一次性小手枪'] = items.get('一次性小手枪', 0) + 1
            save_data(user_path, user_data)
            await message.finish("你发现了其他探险者在此遗落的一个一次性小手枪"+diamond_text+hourglass_text, at_sender=True)
        
        elif 501 <= rnd_tool <= 680:
            items['充能陷阱'] = items.get('充能陷阱', 0) + 1
            save_data(user_path, user_data)
            await message.finish("你发现了其他探险者在此遗落的一个充能陷阱"+diamond_text+hourglass_text, at_sender=True)
        
        elif 681 <= rnd_tool <= 840:
            carrot_rnd = random.randint(1, 10)
            if carrot_rnd > 2:
                items['胡萝卜'] = items.get('胡萝卜', 0) + 1
                save_data(user_path, user_data)
                await message.finish("你发现了其他探险者在此遗落的一个胡萝卜，看起来还很新鲜，还能用。"+diamond_text+hourglass_text, at_sender=True)
            else:
                save_data(user_path, user_data)
                await message.finish("你发现了其他探险者在此遗落的一个胡萝卜，但是看起来变质用不了了"+diamond_text+hourglass_text, at_sender=True)
        
        elif 841 <= rnd_tool <= 860:
            items['madeline提取器'] = items.get('madeline提取器', 0) + 1
            save_data(user_path, user_data)
            await message.finish("你发现了其他探险者在此遗落的一个madeline提取器"+diamond_text+hourglass_text, at_sender=True)

        elif 861 <= rnd_tool <= 880:
            items['时间秒表'] = items.get('时间秒表', 0) + 1
            save_data(user_path, user_data)
            await message.finish("你发现了其他探险者在此遗落的一个时间秒表"+diamond_text+hourglass_text, at_sender=True)
            
        elif 881 <= rnd_tool <= 940:
            items['道具盲盒'] = items.get('道具盲盒', 0) + 1
            save_data(user_path, user_data)
            await message.finish("你发现了其他探险者在此遗落的一个道具盲盒"+diamond_text+hourglass_text, at_sender=True)
            
        elif 941 <= rnd_tool <= 1000:
            items['万能解药'] = items.get('万能解药', 0) + 1
            save_data(user_path, user_data)
            await message.finish("你发现了其他探险者在此遗落的一个万能解药"+diamond_text+hourglass_text, at_sender=True)
            
    #受伤事件
    elif(rnd<=250):
        helmat = collections.get('矿工头盔', 0)
        rnd_safe = 3 if helmat < 1 else random.randint(1, 3)
        if rnd_safe <= 1:
            return
        #有迅捷正常抓
        if user_info['buff2'] == 'speed':
            return
        # 处理buff2状态逻辑
        user_data = buff2_change_status(user_data, user_id, "lucky", 1)
        user_info = user_data.get(user_id,{})
        #受伤1.5小时，在此期间什么都干不了
        next_time = current_time + datetime.timedelta(minutes=89 if collections.get("回想之核", 0) >= 1 else 90)
        user_info['buff'] = 'hurt'
        #加入山洞被困名单
        stuck_data[user_id] = '3'
        #检测星钻
        if diamond_text:
            next_time = current_time  # 立即重置冷却时间
            del stuck_data[user_id]
            user_info['buff'] = 'normal'
        user_info['next_time'] = next_time.strftime("%Y-%m-%d %H:%M:%S")
        #写入主数据表
        save_data(user_path, user_data)
        #写入山洞被困名单
        save_data(stuck_path, stuck_data)

        #随机事件文本
        text = [
            "你一不小心碰到了TNT触发器，被炸了个半死！",
            "你在爬天花板的时候，突然天花板塌了把你砸晕了！",
            "你在丢炸弹的时候没掌握好后坐力，结果一不小心掉到坑里去了！",
            "你在移动的板子上没站稳，掉下去被刺儿扎得满身疮痍！"
        ]
        #发送消息
        await message.finish(random.choice(text)+"你需要原地等待90分钟，或者使用急救包自救，又或者等待他人来救你……"+diamond_text+hourglass_text, at_sender=True)
        
    #挖矿事件
    elif(rnd<=350 + rnd_regu): #35
        #负面buff检测逻辑
        if user_info['debuff'] == 'unlucky':
            return
        
        #遇到水晶矿
        rnd_crystal = random.randint(1,100)
        if(rnd_crystal <= 50):
            #奖励草莓
            berry = 100
            user_info['berry'] += berry             
            #写入主数据表
            save_data(user_path, user_data)
            #发送消息
            await message.finish(f"呀，你在矿洞里发现了一个小型翡翠矿。\n这种是较为常见的绿色翡翠，不过作为翡翠来讲也是很值钱了。\n本次奖励{berry}颗草莓！"+diamond_text+hourglass_text, at_sender=True)
        elif(rnd_crystal <= 90):
            #奖励草莓
            berry = 200
            user_info['berry'] += berry
            #写入主数据表
            save_data(user_path, user_data)
            #发送消息
            await message.finish(f"呀，你在矿洞里发现了一个小型翡翠矿。\n这种是不太常见的白色翡翠，是较为珍贵的翡翠之一。\n本次奖励{berry}颗草莓！"+diamond_text+hourglass_text, at_sender=True)
        elif(rnd_crystal <= 100):
            #奖励草莓
            berry = 500
            user_info['berry'] += berry
            #写入主数据表
            save_data(user_path, user_data)
            #发送消息
            await message.finish(f"呀，你在矿洞里发现了一个小型翡翠矿。\n这种是相当稀有的紫色翡翠，是极为珍贵的翡翠之一。\n本次奖励{berry}颗草莓！"+diamond_text+hourglass_text, at_sender=True)
        else:
            return
    #debuff事件
    elif(rnd<=500+rnd_regu): #50
        #首先玩家没有buff/debuff时才会随机触发
        #有药水状态正常抓
        if user_info['buff2'] != 'normal':
            return
        #有debuff正常抓
        if user_info['debuff'] != 'normal':
            return
        # 检测磁力吸附手套
        spider = collections.get("磁力吸附手套", 0)
        # 检测到了就有1/3的概率避免debuff
        if spider >= 1 and random.randint(1, 3) == 1:
            return
        # 负面buff增加幸运次数
        # 处理buff2状态逻辑
        user_data = buff2_change_status(user_data, user_id, "lucky", 1)
        user_data = buff2_change_status(user_data, user_id, "speed", 1)
        user_info = user_data.get(user_id,{})
        #判断是否开辟恢复时间栏
        if(not 'next_recover_time' in user_info):
            user_info['next_recover_time'] = current_time.strftime("%Y-%m-%d %H:%M:%S")
        # debuff不加时间
        next_time = current_time
        user_info['next_time'] = next_time.strftime("%Y-%m-%d %H:%M:%S")
        rnd_debuff = random.randint(1,3)
        recover_hour = random.randint(2,4)
        if rnd_debuff==1:
            #设定恢复时长为4小时后
            next_recover_time = current_time + datetime.timedelta(hours=recover_hour)
            user_info['next_recover_time'] = next_recover_time.strftime("%Y-%m-%d %H:%M:%S")
            user_info['debuff'] = 'illusory'
            save_data(user_path, user_data)
            await message.finish(f"你不小心走到了矿洞中氧气稀薄的地方，你感觉很难受，似乎{recover_hour}小时内无法再抓到道具了。\n不过幸运地，这{recover_hour}小时内你应该不会获得其他debuff了。", at_sender=True)
        elif rnd_debuff==2:
            #设定恢复时长为4小时后
            next_recover_time = current_time + datetime.timedelta(hours=recover_hour)
            user_info['next_recover_time'] = next_recover_time.strftime("%Y-%m-%d %H:%M:%S")
            user_info['debuff'] = 'poisoned'
            save_data(user_path, user_data)
            await message.finish(f"矿洞的墙壁上的植物似乎在释放有毒气体，你中毒了，抓madeline能力只剩1成，接下来{recover_hour}小时内在抓到madeline时不会获得草莓了。\n不过幸运地，这{recover_hour}小时内你应该不会获得其他debuff了。", at_sender=True)
        elif rnd_debuff==3:
            #设定恢复时长为4小时后
            next_recover_time = current_time + datetime.timedelta(hours=recover_hour)
            user_info['next_recover_time'] = next_recover_time.strftime("%Y-%m-%d %H:%M:%S")
            user_info['debuff'] = 'unlucky'
            save_data(user_path, user_data)
            await message.finish(f"你不知道怎么回事，感觉像是被矿洞内的脏东西附身了，似乎有点不幸，接下来{recover_hour}小时内你不会再挖到翡翠矿了了。\n不过幸运地，这{recover_hour}小时内你应该不会获得其他debuff了。", at_sender=True)
    #遇到被困人员
    elif(rnd <= 600+rnd_regu): #60
        if(len(stuck_data) >= 1):
            save_id = random.choice(list(stuck_data.keys()))
            if(stuck_data[save_id]!='3'): return
            # 发放100草莓
            user_info['berry'] += 100
            # 确保被救者也存在于主数据中
            rescue_user = user_data.setdefault(save_id, {})
            rescue_user['next_time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            del stuck_data[save_id]
            #写入主数据表
            save_data(user_path, user_data)
            #写入被困名单
            save_data(stuck_path, stuck_data)
            await message.finish(f"恭喜你救出了矿洞里的"+ MessageSegment.at(save_id) +"。\n本次奖励100草莓"+ diamond_text+hourglass_text, at_sender=True)
        else:
            #没有需要救的人就结束事件，正常抓madeline
            return
    #紫晶魄
    elif(rnd<=610+rnd_regu):#61
        #是否已经持有藏品"紫晶魄"
        if(not '紫晶魄' in collections):
            collections['紫晶魄'] = 1
            #写入主数据表
            save_data(user_path, user_data)
            await message.finish("你从矿洞深处捡起一块紫色晶体，它的表面微微发光，散发着一种独特的能量。这时，你感到一股难以言喻的力量在你体内流动。\n输入.cp 紫晶魄 以查看具体效果"+ diamond_text+hourglass_text, at_sender=True)
        #否则就是正常抓
        else:
            return
    #矿工头盔
    elif(rnd<=620+rnd_regu):#62
        #是否已经持有藏品"矿工头盔"
        if(not '矿工头盔' in collections):
            collections['矿工头盔'] = 1
            #写入主数据表
            save_data(user_path, user_data)
            await message.finish("你发现了一顶矿工头盔，头盔上的灯光微微闪烁，为你指引前方的道路。即使在黑暗的矿洞中，它也能为你带来光明和安全。\n输入.cp 矿工头盔 以查看具体效果"+ diamond_text+hourglass_text, at_sender=True)
        #否则就是正常抓
        else:
            return
    #调律器
    elif(rnd<=625+rnd_regu):
        #是否已经持有藏品"调律器"
        if(not '调律器' in collections):
            collections['调律器'] = 1
            #写入主数据表
            save_data(user_path, user_data)
            await message.finish("你感到一阵微妙的波动，似乎空气中有某种力量在流动。一件金属质感的仪器悄然出现在你手中，散发出微弱的光辉。\n输入.cp 调律器 以查看具体效果"+ diamond_text+hourglass_text, at_sender=True)
        #否则就是正常抓
        else:
            return
    #回想之核
    elif(rnd<=626+rnd_regu):
        #是否已经持有藏品"回想之核"
        if(not '回想之核' in collections):
            collections['回想之核'] = 1
            #写入主数据表
            save_data(user_path, user_data)
            await message.finish("你在探索之时，突然一颗光辉璀璨的核心缓缓漂浮到你掌心。它散发着奇异的光芒，仿佛能带来超凡的力量。\n输入.cp 回想之核 以查看具体效果"+ diamond_text+hourglass_text, at_sender=True)
        #否则就是正常抓
        else:
            return
    #星光乐谱
    elif(rnd<=629+rnd_regu):
        #是否已经持有藏品"星光乐谱"
        if(not '星光乐谱' in collections):
            collections['星光乐谱'] = 1
            #写入主数据表
            save_data(user_path, user_data)
            await message.finish("在矿洞深处，你无意间发现了一块被岁月掩埋的石板。掀开尘土，你看见一份微弱发光的乐谱，纸页上星光闪烁，仿佛诉说着未知的故事。你小心地拾起它，感受到一股神秘的力量在你手心涌动。\n输入.cp 星光乐谱 以查看具体效果"+ diamond_text+hourglass_text, at_sender=True)
        #否则就是正常抓
        else:
            return
    #商人
    elif(rnd<=700+rnd_regu):
        data3 = open_data(user_list3)
        if user_id not in data3:
            return
        
        #遇见商人不扣幸运
        # 处理buff2状态逻辑
        user_data = buff2_change_status(user_data, user_id, "lucky", 1)
        user_data = buff2_change_status(user_data, user_id, "speed", 1)
        user_info = user_data.get(user_id,{})
        
        #变更事件为交易中
        user_info['event'] = 'trading'
        
        #在该用户拥有的madeline列表里抽取一个拥有的madeline
        k1 = random.choice(list(data3[user_id].keys()))
        k = k1.split('_')
        level = int(k[0]) #抽取的madeline等级
        num = k[1] #抽取的madeline的ID
        #胡萝卜池的madeline低价收购
        if [level, int(num)] in rabbit_madeline3:
            priceRate = 0.8
        else:
            priceRate = 1
        name = madeline_data3.get(str(level)).get(num).get('name') #获取该madeline的名称
        #规定单价和数量
        if level == 1:
            price = random.randint(10,30)
            amount = random.randint(1,5)
        elif level == 2:
            price = random.randint(15,40)
            amount = random.randint(1,4)
        elif level == 3:
            price = random.randint(25,65)
            amount = random.randint(1,3)
        elif level == 4:
            price = random.randint(65,180)
            amount = random.randint(1,2)
        elif level == 5:
            price = random.randint(180,350)
            amount = 1
        else:
            raise KeyError("Invalid level number")
        
        price = math.floor(price * priceRate)
        #交易属性栏要加入3个键值对：交易数量，交易单价，交易物品
        user_info['trade']['数量'] = amount
        user_info['trade']['单价'] = price
        user_info['trade']['物品'] = [int(liechang_number),k1] #存储为[猎场号，madeline属性]
        user_info['event'] = 'trading'
        current_time = datetime.datetime.now()
        next_time = current_time
        user_info['next_time'] = next_time.strftime("%Y-%m-%d %H:%M:%S")
        #写入主数据表
        save_data(user_path, user_data)
        await message.finish(f"你遇到了一位流浪商人，他似乎想从你这里买点东西\n"+
                             f"“你好啊，我在收集一些madeline。现在我需要{amount}个{name}”，我听说这好像是个{level}级的madeline，所以我愿意以每个madeline {price}草莓的价格收购，不知你是否愿意。”\n"+
                             "只有拥有足够的该madeline才可确定交易，并且只能一次性卖完，不支持分批出售\n"+
                             "输入.confirm 确定出售，输入.deny 拒绝本次交易", at_sender=True)
    else:
        return


#四号猎场事件
async def LabStuck(user_data, user_id, message, diamond_text, hourglass_text):
    # 初始化默认值
    user_id = str(user_id)
    user_info = user_data.setdefault(user_id, {})
    user_info.setdefault('berry', 0)
    collections = user_info.setdefault("collections", {})
    items = user_info.setdefault("item", {})
    user_info.setdefault("buff2", "normal")
    user_info.setdefault("compulsion_count", 0)
    user_info.setdefault("event", "nothing")
    user_info.setdefault("trade", {})
    energy = user_info.setdefault("energy", 0)
    liechang_number = user_info.get('lc', '1')
    current_time = datetime.datetime.now()
    
    bot = get_bot()
    #打开矿洞被困名单
    stuck_data = open_data(stuck_path)
    # 读取猎场数据
    kc_data = [open_data(user_list1), open_data(user_list2), open_data(user_list3)]
    # 检查前三个猎场是否满足 PVP 门槛
    if not all(check_liechang(user_id, data) for data in kc_data):
        # 处理buff2状态逻辑
        user_data = buff2_change_status(user_data, user_id, "lucky", 1)
        user_data = buff2_change_status(user_data, user_id, "speed", 1)
        user_info = user_data.get(user_id,{})
        user_info['next_time'] = current_time.strftime("%Y-%m-%d %H:%M:%S")
        save_data(user_path, user_data)
        await message.finish(
            "大门前的激光挡住了你的去路……\n"
            "没准，这些激光是检测你是否满足指定的Madeline条件？",
            at_sender=True
        )
    #判定安定之音，音矿，残片总价值是否达到了15000
    count_canpian = items.get('残片', 0)
    count_anding = items.get('安定之音', 0)
    count_yinkuang = items.get('音矿', 0)
    # 计算总价值
    total_value = (count_canpian * item['残片'][0] +
                   count_anding * item['安定之音'][0] +
                   count_yinkuang * item['音矿'][0])
    if total_value < 15000:
        # 处理buff2状态逻辑
        user_data = buff2_change_status(user_data, user_id, "lucky", 1)
        user_data = buff2_change_status(user_data, user_id, "speed", 1)
        user_info = user_data.get(user_id,{})
        user_info['next_time'] = current_time.strftime("%Y-%m-%d %H:%M:%S")
        save_data(user_path, user_data)
        await message.finish("在地下终端的大门前，你发现门上有三个图案：音符，玻璃碎片和水晶。\n" +
                             "你似乎明白这几个图案的意思了，然后把对应的物品放了上去，但是却没有任何动静，或许是你背包里面对应的物品总价值不够？\n"+
                             f"你目前拥有的对应物品总价值为：{total_value}", at_sender=True)

    # 检测是否已拥有 madeline 飞升器
    if "madeline飞升器" not in collections:
        # 处理buff2状态逻辑
        user_data = buff2_change_status(user_data, user_id, "lucky", 1)
        user_data = buff2_change_status(user_data, user_id, "speed", 1)
        user_info = user_data.get(user_id,{})
        
        if energy < 50000:
            user_info['next_time'] = current_time.strftime("%Y-%m-%d %H:%M:%S")
            save_data(user_path, user_data)
            await message.finish(
                f"你打开了大门，突然发现地上有一个巨大的、奇怪的机械装置，上面有三个空位。\n"
                f"而在机械装置的后面有一道屏障，看起来要激活这个机器才能继续前行。\n"
                f"可是当你激活这个机械装置的时候，却没有任何反应，或许可能需要有足够的能量给它充能才能激活它。\n"
                f"你目前拥有能量的数量为: {energy}",
                at_sender=True
            )

        # 扣除能量并添加 madeline 飞升器
        user_info["energy"] -= 50000
        collections["madeline飞升器"] = 1
        # 不加时间
        next_time = current_time
        user_info['next_time'] = next_time.strftime("%Y-%m-%d %H:%M:%S")
        # 写入数据
        save_data(user_path, user_data)

        await message.finish(
            "你打开了大门，突然发现地上有一个巨大的、奇怪的机械装置，上面有三个不同颜色的凹槽，分别为：红色、绿色、黄色。\n"
            "除此之外，在机器的内部还有三个空位。\n"
            "而在机械装置的后面有一道屏障，看起来要激活这个机器才能继续前行。\n"
            "你将50000点能量投入机器后，机器轰隆隆地运转了起来，后面的屏障也打开了。\n"
            "突然，你感到一股心悸，一股巨大的能量蔓延在了地下终端的各处，你现在感觉到十分乏力。\n"
            "在这个猎场中，抓玛德琳的消耗类道具和祈愿都被封印了，并且你在这个猎场只能正常抓到1、2级的玛德琳。\n"
            "而更高级的玛德琳可能需要用面前这个巨大的机械装置来进行获取了。\n"
            "同时，音矿等提高概率的道具在本猎场也突然暗淡了下来。\n"
            "可能要触发某个条件后才能解除封印？\n"
            "输入 .cp madeline飞升器 以查看这个巨大的机械装置的具体效果。",
            at_sender=True
        )

    #否则就是继续进行其它事件

    ######其他事件#####
    rnd = random.randint(1,1000)
    # 测试
    # if user_id in bot_owner_id:
    #     rnd = 540
    if(rnd<=75):
        #有迅捷正常抓
        if user_info['buff2'] == 'speed':
            return
        # 处理buff2状态逻辑
        user_data = buff2_change_status(user_data, user_id, "lucky", 1)
        user_info = user_data.get(user_id,{})
        #受伤2小时，在此期间什么都干不了
        next_time = current_time + datetime.timedelta(minutes=119 if collections.get("回想之核", 0) >= 1 else 120)
        user_info['buff'] = 'hurt'
        #加入被困名单
        stuck_data[user_id] = '4'
        #检测星钻
        if diamond_text:
            next_time = current_time  # 立即重置冷却时间
            del stuck_data[user_id]
            user_info['buff'] = 'normal'
        user_info['next_time'] = next_time.strftime("%Y-%m-%d %H:%M:%S")
        #写入主数据表
        save_data(user_path, user_data)
        #写入被困名单
        save_data(stuck_path, stuck_data)

        #随机事件文本
        text = [
            "你在穿越蓝色激光的时候，一不小心冲刺了，蓝色激光把你烧的头晕眼涨！",
            "你在穿越橙色激光的时候，一不小心没冲刺，橙色激光把你烧的浑身发烫！",
            "你在撞那些移动方块的时候，突然其中的一个方块长出了刺儿，你被扎的头破血流！",
            "你站在移动方块上面，突然踉跄了一下没站稳，掉到下面的酸液里去了！酸液把你烫的嗷嗷直叫！"
        ]
        #发送消息
        await message.finish(random.choice(text)+"你需要原地疗伤120分钟，或者使用急救包自救……" + diamond_text+hourglass_text, at_sender=True)
        
    # 草莓酱事件
    elif rnd <= 175: 
        # 初始化草莓果酱数量
        items.setdefault("草莓果酱", 0)
        # 负面buff检测
        debuff = user_info.setdefault("debuff", "normal")
        if debuff == "notjam":
            return
        # 生成草莓果酱数量
        rnd_jam = random.randint(1, 100)
        jam_data = [
            (50, 1, "你在终端内探险的时候，发现了一个小型实验室。你在实验室里面发现了别人没有带走的一瓶果酱"),
            (75, 2, "你在终端内探险的时候，发现了一个中型发电厂。你从发电厂里面偷偷拿走了两瓶果酱"),
            (90, 3, "你在终端内探险的时候，发现了一个大型保险柜。你费劲千辛万苦从保险柜里面拿出了三瓶果酱"),
            (100, 4, "你在终端内探险的时候，发现了一个巨型研究所。在你（被自愿）帮助研究所里的人们做完研究后，他们慷慨的送给你了四瓶果酱"),
        ]
        for threshold, count, text in jam_data:
            if rnd_jam <= threshold:
                jam_count, jam_text = count, text
                break

        # 增加果酱数量
        items["草莓果酱"] += jam_count

        # 保存数据
        save_data(user_path, user_data)
        await message.finish(jam_text + diamond_text+hourglass_text, at_sender=True)
    #debuff事件
    elif(rnd<=350): #50
        #首先玩家没有buff/debuff时才会随机触发
        #有药水状态正常抓
        if user_info['buff2'] != 'normal':
            return
        #有debuff正常抓
        if user_info['debuff'] != 'normal':
            return
        # 检测磁力吸附手套
        spider = collections.get("磁力吸附手套", 0)
        # 检测到了就有1/3的概率避免debuff
        if spider >= 1 and random.randint(1, 3) == 1:
            return
        # 负面事件不消耗幸运
        # 处理buff2状态逻辑
        user_data = buff2_change_status(user_data, user_id, "lucky", 1)
        user_data = buff2_change_status(user_data, user_id, "speed", 1)
        user_info = user_data.get(user_id,{})
        #判断是否开辟恢复时间栏
        if(not 'next_recover_time' in user_info):
            user_info['next_recover_time'] = current_time.strftime("%Y-%m-%d %H:%M:%S")
        # debuff不加时间
        next_time = current_time
        user_info['next_time'] = next_time.strftime("%Y-%m-%d %H:%M:%S")
        rnd_debuff = random.randint(1,4) # 暂时关闭失神debuff
        # rnd_debuff = random.randint(1,6)
        # # 测试
        # if user_id in bot_owner_id:
        #     rnd_debuff = 4
        #设定恢复时长为3-6小时后
        recover_hour = random.randint(3,6)
        if rnd_debuff==1:
            #设定恢复时长为3-6小时后
            next_recover_time = current_time + datetime.timedelta(hours=recover_hour)
            user_info['next_recover_time'] = next_recover_time.strftime("%Y-%m-%d %H:%M:%S")
            user_info['debuff'] = 'weaken'
            save_data(user_path, user_data)
            await message.finish(f"你在摧毁机器人进行灵魂转移的时候，一不小心灵魂进入虚弱状态了，接下来{recover_hour}小时内你只能抓到1级的Madeline了。\n不过幸运地，这{recover_hour}小时内你应该不会获得其他debuff了。", at_sender=True)
        elif rnd_debuff==2:
            #设定恢复时长为3-6小时后
            next_recover_time = current_time + datetime.timedelta(hours=recover_hour)
            user_info['next_recover_time'] = next_recover_time.strftime("%Y-%m-%d %H:%M:%S")
            user_info['debuff'] = 'notjam'
            save_data(user_path, user_data)
            await message.finish(f"你在帮助研究所里的人做实验的时候逃跑了，接下里的{recover_hour}h内他们对你进行通缉，你似乎没办法从本猎场拿到果酱了。\n不过幸运地，这{recover_hour}小时内你应该不会获得其他debuff了。", at_sender=True)
        elif rnd_debuff==3:
            #设定恢复时长为3-6小时后
            next_recover_time = current_time + datetime.timedelta(hours=recover_hour)
            user_info['next_recover_time'] = next_recover_time.strftime("%Y-%m-%d %H:%M:%S")
            user_info['debuff'] = 'poisoned_2'
            save_data(user_path, user_data)
            await message.finish(f"你在路过毒水池的时候，一不小心有毒气体吸入过多，你中毒了，接下来{recover_hour}h内抓Madeline获得不了任何草莓了。\n不过幸运地，这{recover_hour}小时内你应该不会获得其他debuff了。", at_sender=True)
        elif rnd_debuff==4:
            #设定恢复时长为3-6小时后
            next_recover_time = current_time + datetime.timedelta(hours=recover_hour)
            user_info['next_recover_time'] = next_recover_time.strftime("%Y-%m-%d %H:%M:%S")
            user_info['debuff'] = 'clumsy'
            save_data(user_path, user_data)
            await message.finish(f"突然，一股神秘的力量侵入了你的身体，除了万能解药以外的几乎全部能够主动使用的道具/藏品都失效了！接下来{recover_hour}小时内你无法使用任何道具了！。\n不过幸运地，这{recover_hour}小时内你应该不会获得其他debuff了。", at_sender=True)
        # elif rnd_debuff==5:
        #     #设定恢复时长为3-6小时后
        #     next_recover_time = current_time + datetime.timedelta(hours=recover_hour)
        #     user_info['next_recover_time'] = next_recover_time.strftime("%Y-%m-%d %H:%M:%S")
        #     user_info['debuff'] = 'tentacle'
        #     save_data(user_path, user_data)
        #     await message.finish(f"你一不小心失足被机械触手绑走了！你被触手玩弄的浑身疲软，毫无精力！接下来{recover_hour}小时内你无法进行任何game/ggl/竞技场等行动了！\n不过幸运地，这{recover_hour}小时内你应该不会获得其他debuff了。", at_sender=True)
        # elif rnd_debuff==6:
        #     next_recover_time = current_time + datetime.timedelta(hours=recover_hour)
        #     user_info['next_recover_time'] = next_recover_time.strftime("%Y-%m-%d %H:%M:%S")
        #     user_info['debuff'] = 'forbidguess'
        #     save_data(user_path, user_data)
        #     # 给小小卒发消息通信
        #     text_rec = f"*forbid_guess {user_id} {recover_hour}"
        #     await bot.send_group_msg(group_id=connect_bot_id, message=text_rec)
        #     await message.finish(f"你一不小心把小小卒推到橙色激光上了，她很生气，惩罚你在接下来{recover_hour}h内无法进行guess/roulette。\n不过幸运地，这{recover_hour}小时内你应该不会获得其他debuff了。", at_sender=True)
        elif rnd_debuff == 5:  # 合并5和6的效果
            # 设定恢复时长为3-6小时后
            next_recover_time = current_time + datetime.timedelta(hours=recover_hour)
            user_info['next_recover_time'] = next_recover_time.strftime("%Y-%m-%d %H:%M:%S")
            user_info['debuff'] = 'tentacle'

            # 给小小卒发消息通信
            text_rec = f"*forbid_guess {user_id} {recover_hour}"
            save_data(user_path, user_data)
            await bot.send_group_msg(group_id=connect_bot_id, message=text_rec)
            await message.finish(
                f"你遭遇了双重不幸！先是被机械触手绑走玩弄到浑身疲软，"
                f"又不小心把小小卒推到橙色激光上惹她生气了！\n"
                f"接下来{recover_hour}小时内你将：\n"
                f"1. 无法进行任何game/ggl/竞技场等行动\n"
                f"2. 无法进行guess/roulette\n"
                f"不过幸运地，这{recover_hour}小时内你应该不会获得其他debuff了。",
                at_sender=True
            )
    
    elif(rnd<=465):#61
        # 暂时关闭小黑屋
        return
        # 负债遇不到这个事件
        if user_info['berry'] < 0:
            return
        # 失神debuff直接返回
        if user_info['debuff'] == 'tentacle':
            return
        # 迅捷状态直接返回
        if user_info['buff2'] == 'speed':
            return
        # ggl和game事件
        #负面事件不消耗幸运
        # 处理buff2状态逻辑
        user_data = buff2_change_status(user_data, user_id, "lucky", 1)
        # user_data = buff2_change_status(user_data, user_id, "speed", 1)
        user_info = user_data.get(user_id,{})
        
        # 不加时间
        next_time = current_time
        user_info['next_time'] = next_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 一半强制抽卡，一半强制game1
        rnd_event = random.randint(1,10)
        if rnd_event <= 5:
            user_info['event'] = 'compulsion_ggl'
            # 抽卡为1-5次随机
            complusion_count = random.randint(1,5)
            bad_event_text = "抽卡"
        else:
            user_info['event'] = 'compulsion_game1'
            # game1为1-3次随机，如果是有事件则没有冷却
            complusion_count = random.randint(1,3)
            bad_event_text = "预言大师"
        # 强制次数随机
        user_info['compulsion_count'] = complusion_count
        #写入主数据表
        save_data(user_path, user_data)
        await message.finish(f"糟糕，一群黑衣人把你强制拉进了一个黑色酒馆，似乎你不满足他们的目标是出不来了！他们现在让你强制进行{bad_event_text}{complusion_count}次！", at_sender=True)
        
    # elif(rnd<=470):
    #     #如果没有，则开辟这一栏并添加
    #     if(not '充能箱' in collections):
    #         collections['充能箱'] = 1
    #         #写入主数据表
    #         save_data(user_path, user_data)
    #         await message.finish("你在备用发电厂的仓库里面发现了一个充能箱，似乎可以给什么东西充能？\n输入.cp 充能箱 以查看具体效果" + diamond_text+hourglass_text, at_sender=True)
        
    #     #否则就是正常抓
    #     else:
    #         return
    elif(rnd<=470):
        #如果没有，则开辟这一栏并添加
        if(not '脉冲雷达' in collections):
            collections['脉冲雷达'] = 1
            #写入主数据表
            save_data(user_path, user_data)
            await message.finish("你在打开一扇门后，布满尘埃的脉冲雷达被放置在了桌上。它似乎平平无奇，所以被人遗忘，从外观上似乎无法看出它的功能。\n输入.cp 脉冲雷达 以查看具体效果" + diamond_text+hourglass_text, at_sender=True)
        
        #否则就是正常抓
        else:
            return
    elif(rnd<=475):
        if(not '磁力吸附手套' in collections):
            user_info['event'] = "getspider"
            #写入主数据表
            save_data(user_path, user_data)
            await message.finish("你在翻看实验室里的日志的时候，从日志本里翻出了一条纸条，上面写着：“Road in Cave”，你似乎有所明悟。" + diamond_text+hourglass_text, at_sender=True)
        #否则就是正常抓
        else:
            return

    elif(rnd<=485):
        #如果没有，则开辟这一栏并添加
        if(not '炸弹包' in collections):
            user_info['event'] = "getbomb"
            #写入主数据表
            save_data(user_path, user_data)
            await message.finish("你在打开开关之时，突然发现这个开关上有一行字：“HOLE IN SANCTUARY”，你似乎有所明悟。" + diamond_text+hourglass_text, at_sender=True)
        #否则就是正常抓
        else:
            return
        
    elif(rnd<=490):
        #如果没有，则开辟这一栏并添加
        if(not '灵魂机器人' in collections):
            collections['灵魂机器人'] = 1
            #写入主数据表
            save_data(user_path, user_data)
            await message.finish("熬夜没头发~ 熬夜没~头~发~\n输入.cp 灵魂机器人 以查看具体效果" + diamond_text+hourglass_text, at_sender=True)
        
        #否则就是正常抓
        else:
            return
    #星钻
    elif(rnd<=491):  # 更低的概率体现其稀有性
        #是否已经持有藏品"星钻"
        if(not '星钻' in collections):
            collections['星钻'] = 1
            #写入主数据表
            save_data(user_path, user_data)
            await message.finish(
                "当你穿过实验室标着『严禁入内』的锈蚀铁门时，"
                "发现废弃的观测台上积着一层诡异的星尘。在灰尘中央，"
                "一颗宝石静静闪烁着，仿佛在呼吸。\n\n"
                "没有仪器，没有电源，但它周身缠绕着银河般的光晕。"
                "你触碰它的刹那，积压多年的疲倦突然像被星光洗净——\n"
                "墙上的老式辐射计量仪疯狂摆动，最终却停在归零的刻度。\n"
                "\n输入.cp 星钻 以查看具体效果" + diamond_text+hourglass_text, 
                at_sender=True
            )
        #否则就是正常抓
        else:
            return
    
    # 获得解药
    elif(rnd<=541):
        water_rnd = random.randint(2,4)
        items['万能解药'] = items.get('万能解药', 0) + water_rnd
        save_data(user_path, user_data)
        await message.finish(f"你在探险的时候，偶然发现地上有{water_rnd}瓶万能解药，会是谁留下来的呢，小小卒吗？" + diamond_text+hourglass_text, at_sender=True)
        
    elif(rnd<=600):
        if(not '黄色球体' in collections):
            return
        data4 = open_data(user_list4)
        if user_id not in data4 :
            return
        #遇见商人不扣幸运
        # 处理buff2状态逻辑
        user_data = buff2_change_status(user_data, user_id, "lucky", 1)
        user_data = buff2_change_status(user_data, user_id, "speed", 1)
        user_info = user_data.get(user_id,{})
        
        #变更事件为交易中
        user_info['event'] = 'trading'
        #交易物品可以是本猎场的madeline或藏品(藏品没写，因为没什么人有)
        #在该用户拥有的madeline列表里抽取一个拥有的madeline
        k1 = random.choice(list(data4[user_id].keys()))
        k = k1.split('_')
        level = int(k[0]) #抽取的madeline等级
        num = k[1] #抽取的madeline的ID
        #胡萝卜池的madeline低价收购
        if [level, int(num)] in rabbit_madeline4:
            priceRate = 0.8
        else:
            priceRate = 1
        name = madeline_data4.get(str(level)).get(num).get('name') #获取该madeline的名称
        #规定单价和数量
        if level == 1:
            price = random.randint(15,40)
            amount = random.randint(1,5)
        elif level == 2:
            price = random.randint(20,50)
            amount = random.randint(1,4)
        elif level == 3:
            price = random.randint(30,70)
            amount = random.randint(1,3)
        elif level == 4:
            price = random.randint(80,200)
            amount = random.randint(1,2)
        elif level == 5:
            price = random.randint(200,400)
            amount = 1
        else:
            raise KeyError("Invalid level number")
        
        price = math.floor(price * priceRate)
        #交易属性栏要加入3个键值对：交易数量，交易单价，交易物品
        user_info['trade']['数量'] = amount
        user_info['trade']['单价'] = price
        user_info['trade']['物品'] = [int(liechang_number),k1] #存储为[猎场号，madeline属性]
        user_info['event'] = 'trading'
        next_time = current_time
        user_info['next_time'] = next_time.strftime("%Y-%m-%d %H:%M:%S")
        #写入主数据表
        save_data(user_path, user_data)
        await message.finish(f"你遇到了一位流浪商人，他似乎想从你这里买点东西\n"+
                             f"“你好啊，我在收集一些madeline。现在我需要{amount}个{name}”，我听说这好像是个{level}级的madeline，所以我愿意以每个madeline {price}草莓的价格收购，不知你是否愿意。”\n"+
                             "只有拥有足够的该madeline才可确定交易，并且只能一次性卖完，不支持分批出售\n"+
                             "输入.confirm 确定出售，输入.deny 拒绝本次交易", at_sender=True)
    else:
        return
