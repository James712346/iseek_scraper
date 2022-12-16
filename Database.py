from tortoise import Tortoise
from asyncio import run
from models import Transit, Graphs
from time import sleep
from scrapper import Iseek

async def DatabaseParser(dataSet):
    # Check if graphID already in database

    graph = await Graphs.get_or_none(ID=dataSet["graphid"])
    timeThreshold = 0 
    if (not graph): 
        graph = await Graphs.create(
                                    ID=dataSet["graphid"],
                                    rawTitle=dataSet["rawTitle"],
                                    **Iseek.titleParse(dataSet["rawTitle"])
                                    )
    else:
        lastRow = await Transit.filter(graph_id = dataSet["graphid"]).order_by("-DateTime").first().values()
        if lastRow: timeThreshold = lastRow['DateTime']
    # Create Transit Model
    modeledData = []
    if not len(dataSet["data"]):
        return []
    print("DATA!")
    previousOutbound = sum(Iseek.ParseRow(dataSet["data"][0])[1:3])
    for data in dataSet["data"]:
        row = Iseek.ParseRow(data)
        if timeThreshold < row[0]:
            
            await Transit.create(
                graph = graph,
                DateTime = row[0],
                Outbound = row[1],
                Inbound = row[2],
                Bandwidth = sum(row[1:3]),
                Bandwidth_RoC = sum(row[1:3]) - previousOutbound / (60*5)
            )
        previousOutbound = sum(row[1:3])
    #Return it
    return modeledData

async def start(IseekInstance:Iseek, DatabaseUrl:str):
    await Tortoise.init(db_url = DatabaseUrl,modules={"models": ["models"]} )
    await Tortoise.generate_schemas()
    while True:
        async with IseekInstance:
            Models = await IseekInstance.getAllData(CustomParser=DatabaseParser,flatten=True, parseTitles=False)
            print("Sent to DB")
        sleep(60*5)
    return None

if __name__ == "__main__":
    import yaml
    with open("config.yaml", "r") as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.Loader)
    Object = Iseek(cfg['Iseek']['username'],cfg['Iseek']['password'],  cfg['Iseek']['realm'], cfg['graphs'], cfg["bandwidthfile"])
    run(start(Object, cfg['databaseURL']))