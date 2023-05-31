from tortoise import Tortoise, exceptions 
from asyncio import run
from models import Transit, Graphs, ScrapeInfo
from scrapper import Iseek
import logging
from time import sleep, time
from sys import stdout
from os import getenv
logger = logging.getLogger("Iseek.database")

ErroredGraphs = []
UPLOADEDANYTHING = False

async def DatabaseParser(dataSet):
    # Check if graphID already in database
    graph = await Graphs.get_or_none(ID=dataSet["graphid"]) # Get Graph Model
    timeThreshold = 0 # Time Threshold for when to start adding data
    # if not in database, create it
    if (not graph): 
        graph = await Graphs.create(
                                    ID=dataSet["graphid"],
                                    rawTitle=dataSet["rawTitle"],
                                    **Iseek.Parse.title(dataSet["rawTitle"])
                                    ) # Create Graph Model
    else:
        lastRow = await Transit.filter(graph_id = dataSet["graphid"]).order_by("-DateTime").first().values() 
        if lastRow: timeThreshold = lastRow['DateTime'].timestamp()
    # Create Transit Model
    modeledData = []
    if not len(dataSet["data"]):
        return []
    logger.debug(f"First Data Point for graph {dataSet['graphid']} \n \t data: {dataSet['data'][0]}")
    offset = 0
    if len(str(dataSet["graphid"])) == 5:
        offset = int(str(dataSet["graphid"])[4:])
        data = dataSet["data"][0].split(",")
        data = ",".join([data[0]] + data[1+offset*2:3+offset*2])
    else:
        data = dataSet["data"][0]
    logger.debug(f"Initial data run {data}")
    previousOutbound = sum(Iseek.Parse.Row(data)[1:3])
    for data in dataSet["data"]:
        logger.debug(f"Parsing data: {data}")
        if offset:
            data = data.split(",")
            data = ",".join([data[0]] + data[1+offset*2:3+offset*2])
            logger.debug(f"Offset Data Transform: {data}")
        try:
            row = Iseek.Parse.Row(data)
        except ValueError:
            ErroredGraphs.append(dataSet["graphid"])
            logger.error(f"{dataSet['graphid']} failed to grab data from iseek, one of the datapoint was NaN")
            logger.error(f"     - Will go to sleep for 30 Seconds to wait for Iseek to update their data")
            sleep(30)
            return [dataSet["graphid"]]
        else:
            if timeThreshold < row[0] and list(map(type, row[1:3])) == [float, float]:
                format_row = {"graph" : graph,
                    "DateTime" : row[0],
                    "Outbound" : row[2],
                    "Inbound" : row[1],
                    "Bandwidth" : round(sum(row[1:3]), 4)}
                RoC = (sum(row[1:3]) - previousOutbound) / (60*5)
                if type(RoC) == float:
                    format_row["Bandwidth_RoC"] = round(RoC, 4)
                logger.debug(f"Adding {format_row} to database")
                try:
                    logger.info(f"Adding {graph} to database")
                    UPLOADEDANYTHING = True
                    await Transit.create(**format_row)
                except exceptions.OperationalError:
                    logger.error(f"Failed to add {format_row} to database")

            previousOutbound = sum(row[1:3])
    #Return it
    return []

async def start(IseekInstance:Iseek, DatabaseUrl:str, usingConfig=False):
    startingTime = time()
    await Tortoise.init(db_url = DatabaseUrl, modules={"models": ["models"]})
    if getenv("no_init") != 'true':
        try:
            await Tortoise.generate_schemas(safe=True)
        except exceptions.OperationalError:
            logger.error("Error when creating the Schema (can ignore if using mssql, as it usally minor)", exc_info=True)
    else:    
        IseekInstance.graphs = await Graphs.all().values_list('ID', flat=True)
    async with IseekInstance:
        Models = await IseekInstance.getAllData(CustomParser=DatabaseParser,flatten=True, parseTitles=False)
        for graph in ErroredGraphs:
            data = await IseekInstance.getData(graph, None, parseTitles=False)
            if await DatabaseParser(data) == [graph]:
                logger.critical(f"Database failed a second time to grab data from {graph}!")
            else:
                ErroredGraphs.remove(graph)
    TimeTaken = time() - startingTime
    logger.info(f"Time Taken: {TimeTaken}")
    if UPLOADEDANYTHING:
        await ScrapeInfo.create(noentries=len(IseekInstance.graphs), noentryfailed=len(ErroredGraphs), timetaken=TimeTaken)
    return None

if __name__ == "__main__":
    handler = logging.StreamHandler(stdout)
    formatter = logging.Formatter(
        '%(asctime)s [%(name)-14s] %(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    Iseek.Logger.addHandler(handler)
    Iseek.Parse.Logger.addHandler(handler)

    logger.propagate = False 
    Iseek.Logger.propagate = False
    Iseek.Parse.Logger.propagate = False
  
    logger.setLevel("INFO")
    logger.info("Starting Database")
    if not getenv("iseek_username"):
        logger.info("Loading config from config.yaml")
        import yaml
        with open("config.yaml", "r") as ymlfile:
            cfg = yaml.load(ymlfile, Loader=yaml.Loader)
    else:
        logger.info("Loading config from local/docker environment variables")
        cfg = {
            "Iseek":{
                "username": getenv("iseek_username"),
                "password": getenv("iseek_password"),
                "realm" : getenv("iseek_realm")
            },
            "databaseURL": getenv("databaseURL"),
            "log":{
                "iseek": getenv("log_iseek"),
                "parse": getenv("log_parse"),
                "database": getenv("log_database")
            }
        }
    if not cfg["log"]["iseek"]:
        cfg["log"]["iseek"] = "INFO"
    if not cfg["log"]["parse"]:
        cfg["log"]["parse"] = "INFO"
    if not cfg["log"]["database"]:
        cfg["log"]["database"] = "INFO"
    Iseek.Logger.setLevel(cfg["log"]["iseek"])
    Iseek.Parse.Logger.setLevel(cfg["log"]["parse"])
    logger.setLevel(cfg["log"]["database"])
    Object = Iseek(cfg['Iseek']['username'],cfg['Iseek']['password'],  cfg['Iseek']['realm'])
    run(start(Object, cfg['databaseURL']))


