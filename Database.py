from tortoise import Tortoise, exceptions
from asyncio import run
from models import Transit, Graphs
from time import sleep
from scrapper import Iseek
import logging

logger = logging.getLogger("Database Module")

async def DatabaseParser(dataSet):
    # Check if graphID already in database

    graph = await Graphs.get_or_none(ID=dataSet["graphid"])
    timeThreshold = 0 
    if (not graph): 
        graph = await Graphs.create(
                                    ID=dataSet["graphid"],
                                    rawTitle=dataSet["rawTitle"],
                                    **Iseek.Parse.title(dataSet["rawTitle"])
                                    )
    else:
        lastRow = await Transit.filter(graph_id = dataSet["graphid"]).order_by("-DateTime").first().values()
        if lastRow: timeThreshold = lastRow['DateTime'].timestamp()
    # Create Transit Model
    modeledData = []
    if not len(dataSet["data"]):
        return []
    previousOutbound = sum(Iseek.Parse.Row(dataSet["data"][0])[1:3])
    for data in dataSet["data"]:
        row = Iseek.Parse.Row(data)
        if timeThreshold < row[0] and list(map(type, row[1:3])) == [float, float]:
            format_row = {"graph" : graph,
                "DateTime" : row[0],
                "Outbound" : row[1],
                "Inbound" : row[2],
                "Bandwidth" : round(sum(row[1:3]), 4)}
            RoC = sum(row[1:3]) - previousOutbound / (60*5)
            if type(RoC) == float:
                format_row["Bandwidth_RoC"] = round(RoC, 4)
            print(format_row)
            await Transit.create(**format_row)

        previousOutbound = sum(row[1:3])
    #Return it
    return modeledData

async def start(IseekInstance:Iseek, DatabaseUrl:str):
    await Tortoise.init(db_url = DatabaseUrl,modules={"models": ["models"]} )
    try:
        await Tortoise.generate_schemas(safe=True)
    except exceptions.OperationalError:
        print("Schemas already created")

    while True:
        async with IseekInstance:
            Models = await IseekInstance.getAllData(CustomParser=DatabaseParser,flatten=True, parseTitles=False)
        sleep(60*5)
    return None

if __name__ == "__main__":
    import yaml
    with open("config.yaml", "r") as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.Loader)
    Object = Iseek(cfg['Iseek']['username'],cfg['Iseek']['password'],  cfg['Iseek']['realm'], cfg['graphs'], cfg["bandwidthfile"])
    run(start(Object, cfg['databaseURL']))