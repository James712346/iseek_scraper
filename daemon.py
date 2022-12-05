
from tortoise import Tortoise
from models import Transit, Graphs
from datetime import datetime
from pytz import timezone
import asyncio
from aiohttp import ClientSession 
from time import sleep


class Iseek:
    TimeZone = timezone("Australia/Brisbane")
    URL = "https://customer.ims.iseek.com.au/"
    ACTION = "graph_xport.php"
    LOGOUT = "logout.php"


    def __init__(self, username, password, realm, databaseURL) -> None:
        self.databaseURL = databaseURL
        self.username = username
        self.password = password
        self.realm = realm

    async def __aenter__(self):
        self.Session = await ClientSession().__aenter__()
        await Tortoise.init(
            db_url=self.databaseURL,
            modules={"models": ["models"]}
        )
        # Generate the schema
        await Tortoise.generate_schemas()
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

    def FindgraphID(self, graphID):
        print(self.Graphs)

    def ParseData(self, DATA_DUMP, timeThreshold=0):
        Parsed_Data = []
        for data in DATA_DUMP:
            data = data.replace('"', '').split(",")
            time = int(datetime.timestamp(Iseek.TimeZone.localize(datetime.strptime(data[0],"%Y-%m-%d %H:%M:%S"))))
            if timeThreshold < time:
                Parsed_Data.append((time, float(data[1]), float(data[2])))
        return Parsed_Data
    
    async def UpdateGraph(self, graphID):
        var = f"?local_graph_id={graphID}&rra_id=5&view_type=tree"
        async with self.Session.post(Iseek.URL+Iseek.ACTION+var) as responce:
            DATA_DUMP = await responce.text()
            DATA_DUMP = DATA_DUMP.split("\n")
            __, IsCreated = await Graphs.get_or_create(ID=graphID, Title =DATA_DUMP[0].replace('"', '').split(",")[1])
            if (IsCreated):
                Data = self.ParseData(DATA_DUMP[10:-1])
            else:
                lastRow = await Transit.filter(graph_id = graphID).order_by("-DateTime").first().values()
                Data = self.ParseData(DATA_DUMP[10:-1], lastRow['DateTime'])
        for data in Data:
            await Transit.create(graph_id=graphID, DateTime=data[0], Outbound=float(data[1]), InBound= float(data[2]))
    
    async def __aexit__(self,exc_type, exc_value, traceback):
        await self.logout()
        await self.Session.__aexit__(exc_type, exc_value, traceback)
        await Tortoise.close_connections()
    
    async def start(instance):
        while True:
            async with instance as iseek:
                print("Updating")
                for graphID in await iseek.GetGraphID():
                    await iseek.UpdateGraph(graphID)
            sleep(5*60)
            

    async def AddGraph(instance, Graphs="./GraphID"):
        async with instance as iseek:
            if type(Graphs) == str:
                with open(Graphs) as f:
                    Graphs = [i.strip() for i in f.readlines()]
            for graphID in Graphs:
                await iseek.UpdateGraph(graphID)

        
if __name__ == "__main__":
    import yaml
    with open("config.yaml", "r") as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.Loader)
    Object = Iseek(cfg['Iseek']['username'],cfg['Iseek']['password'],  cfg['Iseek']['realm'], cfg['databaseURL'])
    asyncio.run(Iseek.AddGraph(Object))
    asyncio.run(Iseek.start(Object))


