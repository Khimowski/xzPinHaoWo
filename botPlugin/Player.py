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