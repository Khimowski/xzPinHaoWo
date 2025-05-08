import nonebot
from nonebot import get_plugin_config, logger
from nonebot.plugin import PluginMetadata

from .config import Config
# from Player import Player
from nonebot import on_command, require, get_bot
from nonebot.adapters import Bot, Event, Message
from nonebot.params import CommandArg
from nonebot.rule import to_me

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from serial import Serial
import json
import os
import sys
import pip
import importlib

__plugin_meta__ = PluginMetadata(
    name="MaimaiYYW",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

#############设置列表##############

COSTPERTIME = 6                           #每小时价格
TIMEFORMAT = "%Y-%m-%d %H:%M:%S"          #出勤退勤记录时长的时间格式
PLACENAME = "拼好窝"                       #音游窝名称
#ser = Serial("COM5", 9600, timeout=1)    #串口设置
ADMINS = {                                #管理员用户列表
167047679,2655548416
}

##################################

scheduler = require('nonebot_plugin_apscheduler').scheduler

class Player:
    def __init__(self, nickname, userid):
        self.__userid = userid       #用户编号 => QQ号
        self.__nickname = nickname   #用户名
        self.__allTime = [0,0,0]     #用户总时长 Day Hrs Min
        self.__balance = 0           #用户剩余金钱
        self.__startTime = 0         #用户出勤开始时间
        self.__status = False        #用户是否出勤
        self.__playing = []          #用户当前游玩机台

    def balanceRechar(self, money):
        self.__balance += money
    def balanceReduce(self, money):
        self.__balance -= money
    def balanceSet(self, money):
        self.__balance = money

    def allTimeAdd(self, time):
        Day = time // 1440
        time = time % 1440
        Hour = time // 60
        Minute = time % 60
        self.__allTime[0] = Day
        self.__allTime[1] = Hour
        self.__allTime[2] = Minute

    def changeName(self, newNickname):
        self.__nickname = newNickname

    def online(self):
        self.__status = True
    def offline(self):
        self.__status = False

    ###set函数###
    def setStartTime(self, time):
        self.__startTime = time

    ###get函数###
    def getDay(self):
        return self.__allTime[0]
    def getHour(self):
        return self.__allTime[1]
    def getMin(self):
        return self.__allTime[2]
    def getMins(self):
        return self.__allTime[0]*1440+self.__allTime[1]*60+self.__allTime[2]
    def getBalance(self):
        return self.__balance
    def getStartTime(self):
        return self.__startTime

    def getUserid(self):
        return self.__userid
    def getNickname(self):
        return self.__nickname
    def getStatus(self):
        return self.__status

def get_time(time1, time2):
    sec = int((time1 - time2).total_seconds())
    return sec // 60 + 1

def sortPlayers():
    sorted_marks = {}
    sorted_users = {}
    max = 0
    maxmark = 0
    for i in range(len(users)):
        max = 0
        maxmark = 0
        for j in users:
            if((users[j].getMins() > max) and (j not in sorted_marks)):
                max = users[j].getMins()
                maxmark = j
        sorted_users[maxmark] = users[maxmark]
        sorted_marks[maxmark] = users[maxmark]

    return sorted_users

def serialize_player(player):
    return {
        "userid": player.getUserid(),
        "nickname": player.getNickname(),
        "allTime": player.getMins(),
        "balance": player.getBalance(),
        "startTime": str(player.getStartTime()),
        "status": player.getStatus(),
    }

# 自定义反序列化函数
def deserialize_player(data):
    player = Player(data["nickname"], data["userid"])
    player.allTimeAdd(data["allTime"])
    player.balanceSet(data["balance"])
    if(data["status"]):
        player.online()
    else:
        player.offline()
    player.setStartTime(datetime.strptime(data["startTime"], TIMEFORMAT))
    return player

###个人命令###
user_help     = on_command("帮助", rule=to_me(), aliases={"help"})
user_register = on_command("注册", rule=to_me(), aliases={"创建账号"})
user_ranklist = on_command("排行", rule=to_me())
user_info     = on_command("我的", rule=to_me(), aliases={"查询","info"})
user_rename   = on_command("改名", rule=to_me())

###窝内命令###
check_maimai  = on_command("场况", rule=to_me(), aliases={"phwj","几个人"})
start_maimai  = on_command("出勤", rule=to_me(), aliases={"cq"})
stop_maimai   = on_command("退勤", rule=to_me(), aliases={"tq"})
open_door     = on_command("开门", rule=to_me(), aliases={"km"})

###管理命令###
admin_addbalance = on_command("增加余额", rule=to_me(), aliases={"添加余额","充值余额"})
admin_setbalance = on_command("设置余额", rule=to_me(), aliases={"更改余额"})
admin_dowSave    = on_command("保存存档",rule=to_me())
admin_getSave    = on_command("读取存档", rule=to_me(), aliases={"恢复存档"})
admin_stop       = on_command("管理退勤", rule=to_me())

user_times = {} #单次出勤时长统计
users = {}      #用户列表

@scheduler.scheduled_job(CronTrigger.from_crontab("0 8 * * *"))
async def scheduled_job():
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"maimai_{today}.sav"
    bot = get_bot()

    serialized_users = {qq: serialize_player(player) for qq, player in users.items()}
    try:
        with open(filename, "w", encoding="UTF-8") as f:
            json.dump(serialized_users, f, ensure_ascii=False, indent=4)
        await bot.send_group_message(message=f"数据已保存至 {filename}")
    except Exception as e:
        await bot.send_group_message(message=f"保存时发生错误:{e}")



@user_help.handle()
async def _(bot: Bot, event: Event):
    logger.info("触发指令【用户帮助】")
    await user_help.send("""  --个人相关--
创建账号: /注册 [昵称] 或 /创建账号 [昵称]
查询信息: /我的 或 /查询 [id]
查询排行: /排行

  --出勤相关--
出勤: /出勤 或 /cq
退勤: /退勤 或 /tq
开门: /开门 或 /km
""")
    await user_help.finish()

@user_info.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    if user_id := args.extract_plain_text():
        user_id = int(user_id)
    else:
        user_id = int(event.get_user_id())

    if(user_id not in users):
        await user_info.finish(f"{user_id} 尚未注册")

    thisUser = users[user_id]
    await user_info.send(f"""
————————个人信息————————
用户编号:{user_id}
用户昵称:{thisUser.getNickname()}
用户状态:{"出勤" if thisUser.getStatus() else "退勤"} {f"\n开始时间:{thisUser.getStartTime()}" if thisUser.getStatus() else ""}
用户余额:{thisUser.getBalance()}
游玩时长:{thisUser.getDay()}天{thisUser.getHour()}小时{thisUser.getMin()}分钟""")
    await user_info.finish()

@user_ranklist.handle()
async def _(bot: Bot, event: Event):
    sorted_users = sortPlayers()
    count = 0
    message = ""
    for id in sorted_users:
        user = sorted_users[id]
        count += 1
        message += f"{count}. {user.getNickname()} : {user.getDay()}天{user.getHour()}小时{user.getMin()}分钟\n"
        if count % 10 == 0:
            break

    await user_ranklist.finish(message)

@user_register.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    user_id = int(event.get_user_id())

    if nickname := args.extract_plain_text():
        pass
    else:
        nickname = f"{PLACENAME}用户{len(users)+1}"
    users[user_id] = Player(nickname, user_id)
    logger.debug(users)
    await user_register.finish(message=f"创建账号成功，玩家 {user_id} 的昵称为 {users[user_id].getNickname()}")

@user_rename.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    user_id = int(event.get_user_id())
    if nickname := args.extract_plain_text():
        pass
    else:
        await user_rename.finish("请输入新昵称")

    if user_id not in users:
        await user_rename.finish(f"{user_id} 尚未注册")

    users[user_id].changeName(nickname)
    await user_rename.finish(f"{user_id} 的昵称已改为 {users[user_id].getNickname()}")


@start_maimai.handle()
async def _(bot: Bot, event: Event):
    user_id = int(event.get_user_id())
    time = datetime.now().strftime(TIMEFORMAT)
    time = datetime.strptime(time, TIMEFORMAT)
    if user_id not in users:
        await start_maimai.finish(message=f"您尚未注册，请先创建账号")

    thisUser = users[user_id]

    if thisUser.getBalance() < -10:
        await start_maimai.finish(message=f"出勤失败，{thisUser.getNickname()}[{user_id}] 欠费超过10元")

    await start_maimai.send(message="请不要大力拍打或滑动哦")
    if not thisUser.getStatus():
        thisUser.online()
        users[user_id].setStartTime(time)
        await start_maimai.finish(message=f"出勤成功，{thisUser.getNickname()}[{user_id}] 于 {time} 开始出勤")
    else:
        await start_maimai.finish(message=f"出勤失败，{thisUser.getNickname()}[{user_id}] 已于 {user_times[user_id]} 开始出勤")


@stop_maimai.handle()
async def _(bot: Bot, event: Event):
    user_id = int(event.get_user_id())
    time = datetime.now()
    logger.debug(type(time))
    if user_id not in users:
        await stop_maimai.finish(f"您尚未注册，请先创建账号")

    thisUser = users[user_id]

    await stop_maimai.send("请带好随身物品，当心自动拾取")
    if thisUser.getStatus():
        thisUser.offline()
        duration = get_time(time,users[user_id].getStartTime())
        thisUser.allTimeAdd(duration)
        if(duration % 60 > 10):
            duration = duration // 60 + 1
        else:
            duration = duration // 60
        thisUser.balanceReduce(duration*COSTPERTIME)
        await stop_maimai.finish(f"出勤结束，{thisUser.getNickname()}[{user_id}] 本次出勤时长 {duration} 小时")
    else:
        await stop_maimai.finish(f"{thisUser.getNickname()}[{user_id}] 还没出勤呢")

@open_door.handle()
async def _(bot: Bot, event: Event):
    user_id = int(event.get_user_id())
    time = datetime.now()
    if user_id not in users:
        await open_door.finish(f"您尚未注册，请先创建账号")

    thisUser = users[user_id]
    if (thisUser.getStatus()):
        #ser.write(b"open\n")
        await open_door.finish(f"门已打开，记得随手关门哦")
    else:
        await open_door.finish(f"您还没出勤呢，先发送 出勤 来出勤吧")


@check_maimai.handle()
async def _(bot: Bot, event: Event):
    num = 0
    message = "当前玩家有:\n"
    for each in users:
        if(users[each].getStatus()):
            num += 1
            message += f"{num}. {users[each].getNickname()}[{each}]\n"

    message += f"当前拼好窝内人数为: {num}"

    if(num == 0):
        await check_maimai.send("当前拼好窝内没有人")
    await check_maimai.finish(message)

@admin_addbalance.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    admin_id = int(event.get_user_id())
    args = args.extract_plain_text().strip().split()
    if(len(args) != 2):
        await admin_addbalance.finish("请按照 增加余额 [QQ号] [金额] 的格式输入")
    user_id, money = args
    user_id = int(user_id)
    if(user_id not in users):
        await admin_addbalance.finish(f"{user_id} 尚未注册")

    if(admin_id not in ADMINS):
        await admin_addbalance.finish(f"{admin_id} 非管理员用户")

    thisUser = users[user_id]
    thisUser.balanceRechar(int(money))
    await admin_addbalance.finish(f"已为 {thisUser.getNickname()}[{user_id}] 添加 {money} 小时时长")

@admin_setbalance.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    admin_id = int(event.get_user_id())
    args = args.extract_plain_text().strip().split()
    if(len(args) != 2):
        await admin_setbalance.finish("请按照 设置余额 [QQ号] [金额] 的格式输入")
    user_id, money = args
    user_id = int(user_id)
    if(user_id not in users):
        await admin_setbalance.finish(f"{user_id} 尚未注册")

    if(admin_id not in ADMINS):
        await admin_setbalance.finish(f"{admin_id} 非管理员用户")

    thisUser = users[user_id]
    thisUser.balanceSet(int(money))
    await admin_setbalance.finish(f"已将 {thisUser.getNickname()}[{user_id}] 的余额设置为 {money} 元")

@admin_stop.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    admin_id = int(event.get_user_id())
    if user_id := args.extract_plain_text():
        if admin_id not in ADMINS:
            await admin_stop.finish(f"{admin_id} 非管理员用户")
        user_id = int(user_id)
        if user_id not in users:
            await admin_stop.finish(f"{user_id} 尚未注册")
        thisUser = users[user_id]
        if users[user_id].getStatus():
            users[user_id].Offline()
            await admin_stop.finish(f"已将 {thisUser.getNickname()}[{user_id}] 退勤")
        else:
            await admin_stop.finish(f"{thisUser.getNickname()}[{user_id}] 尚未出勤")
    else:
        await admin_stop.finish("请按照 管理退勤 [QQ号] 的格式输入")

@admin_dowSave.handle()
async def _(bot: Bot, event: Event):
    admin_id = int(event.get_user_id())
    if admin_id not in ADMINS:
        await admin_dowSave.finish(f"{admin_id} 非管理员")

    filename = f"maimai_{datetime.now().strftime("%Y-%m-%d")}.sav"
    try:
        serialized_users = {qq: serialize_player(player) for qq, player in users.items()}
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(serialized_users, f, ensure_ascii=False, indent=4)
    except Exception as e:
        await admin_dowSave.finish(f"保存时发生错误:{e}")

    await admin_dowSave.finish(f"数据已保存至 {filename}")

@admin_getSave.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    admin_id = int(event.get_user_id())
    if admin_id not in ADMINS:
        await admin_getSave.finish(f"{admin_id} 非管理员用户")

    if filepath := args.extract_plain_text():
        pass
    else:
        save_files = [f for f in os.listdir() if f.startswith("maimai") and f.endswith(".sav")]
        if not save_files:
            await admin_getSave.finish(f"未找到存档")

        filepath = max(save_files, key=lambda f: datetime.strptime(f[7:-4], "%Y-%m-%d"))

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            serialized_users = json.load(f)

        global users
        users = {int(qq): deserialize_player(data) for qq, data in serialized_users.items()}
        logger.debug(users)
    except Exception as e:
        await admin_getSave.finish(f"发生错误:{e}")

    await admin_getSave.finish(f"已读取存档 {filepath}")