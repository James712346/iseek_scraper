from aiohttp import ClientSession 
from asyncio import run as arun
from datetime import datetime
from pytz import timezone
from time import sleep


class Iseek:
    TimeZone = timezone("Australia/Brisbane")
    URL = "https://customer.ims.iseek.com.au/"
    ACTION = "graph_xport.php"
    LOGOUT = "logout.php"


    def __init__(self, username, password, realm, graphs=[]) -> None:
        self.username = username
        self.password = password
        self.realm = realm
        self.graphs = graphs

    async def __aenter__(self):
        self.Session = await ClientSession().__aenter__()
        await self.login()
        return self

    async def GetGraphID(self):
        return await Graphs.all().values_list("ID", flat=True)

    async def login(self):
        payload={
            'action': 'login',
            'login_username': self.username,
            'login_password': self.password,
            'realm': self.realm 
        }
        await self.Session.post(Iseek.URL+Iseek.ACTION, data=payload)

    async def logout(self):
        await self.Session.post(Iseek.URL+Iseek.LOGOUT)


    def ParseData(DATA_DUMP, timeThreshold=0):
        Parsed_Data = []
        for data in DATA_DUMP:
            data = data.replace('"', '').split(",")
            time = int(datetime.timestamp(Iseek.TimeZone.localize(datetime.strptime(data[0],"%Y-%m-%d %H:%M:%S"))))
            if timeThreshold < time:
                Parsed_Data.append((time, float(data[1]), float(data[2])))
        return Parsed_Data
    
    
    async def getData(self, graphID):
        var = f"?local_graph_id={graphID}&rra_id=5&view_type=tree"
        async with self.Session.post(Iseek.URL+Iseek.ACTION+var) as responce:
            DATA_DUMP = await responce.text()
            DATA_DUMP = DATA_DUMP.split("\n")
        return (DATA_DUMP[0].replace('"', '').split(",")[1], DATA_DUMP[10:-1])

    
    async def __aexit__(self,exc_type, exc_value, traceback):
        await self.logout()
        await self.Session.__aexit__(exc_type, exc_value, traceback)
    
    async def start(instance):
        while True:
            async with instance as iseek:
                print("Updating")
                for graphID in await iseek.GetGraphID():
                    await iseek.UpdateGraph(graphID)
            sleep(5*60)
            

    async def AddGraph(instance, Graphs):
        async with instance as iseek:
            for graphID in Graphs:
                await iseek.UpdateGraph(graphID)

        
if __name__ == "__main__":
    print("Giving database some time to start")
    sleep(30) 
    import yaml
    with open("config.yaml", "r") as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.Loader)
    Object = Iseek(cfg['Iseek']['username'],cfg['Iseek']['password'],  cfg['Iseek']['realm'])
    arun(Iseek.AddGraph(Object, cfg['graphs']))
    arun(Iseek.start(Object))


