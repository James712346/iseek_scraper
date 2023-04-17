from aiohttp import ClientSession 
from asyncio import run as arun
from datetime import datetime
from pytz import timezone
import re, logging

bandwidthFile = None



class Iseek:
    TimeZone = timezone("Australia/Brisbane")
    URL = "https://customer.ims.iseek.com.au/"
    ACTION = "graph_xport.php"
    LOGOUT = "logout.php"
    

    Logger = logging.getLogger("Iseek")
    def __init__(self, username:str, password:str, realm:str, graphs={}, bandfile = "") -> None:
        """Initizes the Iseek Scrapper Class, with nessary values to complete tasks 

        Args:
            username (str): Iseek Account Username
            password (str): Iseek Account Password
            realm (str): Which ever service the Iseek Account is connected to, local or LDAP
            graphs (dict, optional): Accept a dictornary with the key being graphID, and value being a dictornary of attibutes ie. {2380: {'state': 'QLD', 'suburb': 'N/A'}}. Defaults to {}.
        """
        __class__.Logger.info("Initizing Iseek scrapper")
        global bandwidthFile
        self.username = username
        self.password = password
        self.realm = realm
        self.graphs = graphs
        bandwidthFile = bandfile
    
    async def __aenter__(self):
        """Used with python's 'with', therefore makes sure this script enters and closes correctly

        Returns:
            Iseek: Returns the iseek object
        """
        self.Session = await ClientSession().__aenter__()
        await self.login()
        return self

    async def login(self):
        """Login into Iseek, and scripts session
        """
        __class__.Logger.info("Logging into Iseek")

        payload={
            'action': 'login',
            'login_username': self.username,
            'login_password': self.password,
            'realm': self.realm 
        }
        await self.Session.post(Iseek.URL+Iseek.ACTION, data=payload)
    
    async def logout(self):
        """Logs out of the Iseek Session
        """
        __class__.Logger.info("Logging out")

        await self.Session.post(Iseek.URL+Iseek.LOGOUT)

    # def ParseData(DATA_DUMP:list[str], timeThreshold=0) -> list[tuple]:
    #     """Loops through that data, parsing it to a state that is easy to use

    #     Args:
    #         DATA_DUMP (list[str]): list of data, received from getData 
    #         timeThreshold (int, optional): Timestamp (in Unix time) of the last entry into the database, so that those, and later entries are skipped. Defaults to 0.

    #     Returns:
    #         list[tuple]: Returns a list containing tuple with a structure of (timestamp, inbound, outbound). Timestamp is formatted in Unix time
    #     """
    #     Parsed_Data = []
    #     previousOutbound = Iseek.ParseRow(DATA_DUMP[0])[2] + Iseek.ParseRow(DATA_DUMP[0])[1]
    #     for data in DATA_DUMP:
    #         row = Iseek.ParseRow(data)
    #         if timeThreshold < row[0]:
    #             BandwidthRoC = ((row[1]+row[2])-previousOutbound) / (60*5) 
    #             row = row + tuple([row[1]+row[2], BandwidthRoC])
    #             Parsed_Data.append(row)
    #         previousOutbound = row[3]
    #     return Parsed_Data
    class Parse:
        Logger = logging.getLogger("Iseek.parser")
        def __init__(DATA_DUMP:list[str], timeThreshold=0, Rowoffset = 0) -> list[tuple]:
            """Loops through that data, parsing it to a state that is easy to use

            Args:
                DATA_DUMP (list[str]): list of data, received from getData 
                timeThreshold (int, optional): Timestamp (in Unix time) of the last entry into the database, so that those, and later entries are skipped. Defaults to 0.

            Returns:
                list[tuple]: Returns a list containing tuple with a structure of (timestamp, inbound, outbound). Timestamp is formatted in Unix time
            """
            Parsed_Data = []
            data = DATA_DUMP[0][0] + DATA_DUMP[0][1+Rowoffset*2:3+Rowoffset*2]
            previousOutbound = sum(Iseek.Parse.Row(data)[1:3])
            for data in DATA_DUMP:
                if Rowoffset:
                    data = data[0] + data[1+Rowoffset*2:3+Rowoffset*2]
                row = Iseek.Parse.Row(data)
                if timeThreshold < row[0]:
                    BandwidthRoC = ((row[1]+row[2])-previousOutbound) / (60*5) 
                    row = row + tuple([row[1]+row[2], BandwidthRoC])
                    Parsed_Data.append(row)
                previousOutbound = row[3]
            return Parsed_Data
        

        def Row(Raw_Row):
            Raw_Row = Raw_Row.replace('"', '').split(",")
            time = int(datetime.timestamp(Iseek.TimeZone.localize(datetime.strptime(Raw_Row[0],"%Y-%m-%d %H:%M:%S"))))
            __class__.Logger.debug(f"rows: {Raw_Row[1]} {Raw_Row[2]}")
            if 'NaN' in (Raw_Row[1], Raw_Row[2]): 
                __class__.Logger.debug(f"[row.check] {float('nan') in (float(Raw_Row[1]), float(Raw_Row[2]))}")
                raise ValueError("NaN is invaild data point")
            return (time, float(Raw_Row[1]), float(Raw_Row[2]))
        
        def title(title):
            dataParsed = { }
            POIstates = {"ldr": "QLD", "gh": "NSW", "ls": "VIC", "md":"WA"}
            states = ["","","NSW", "VIC", "QLD", "SA", "WA", "TAS", "NT", "ACT"]
            core_regex = "([A-Za-z]{2,3})-([A-Za-z]+)-[A-Za-z0-9]+[ -]+(.*) (CSA[0-9]+)[ -]+(CVC[0-9]+)[ -]+(VLK[0-9]+)[ -]+(.*) ([0-9])([A-Za-z]{3})[ -]+(.*)"
            coreBackup_regex = "([A-Za-z]{2,3})-([A-Za-z]+)-[A-Za-z0-9]+[ -]+(.*) (CSA[0-9]+)[ -]+(CVC[0-9]+)[ -]+(VLK[0-9]+)[ -]+(.*)"
            corelimited_regex = "([A-Za-z]{2,3})-([A-Za-z]+)-[A-Za-z0-9]+[ -]+(.*)[ -]+()(CVC[0-9]+)[ -]+()(.*)"
            swc_regex = "([A-Za-z]{2,3})-([A-Za-z0-9]+).* ([0-9])([A-Za-z]{3})"
            swcore_regex = "([A-Za-z]{2,3})-([A-Za-z0-9]+).*port-channel([0-9]+)(?>.+ ([0-9])([A-Z]{3})|).* ([A-Z][a-z]+|VLINK)"
            
            if "swcore" in title:
                __class__.Logger.debug(f"Parsing {title} as a swcore title")

                results = re.search(swcore_regex, title)
                dataParsed["POI_state"] = POIstates[results.group(1)]
                dataParsed["POI_server"] = results.group(2)
                dataParsed["channel"] = results.group(3)
                dataParsed["state"] = POIstates[results.group(1)]
                dataParsed["location"] = results.group(6)
                if (results.group(4)):
                    dataParsed["state"] =states[int(results.group(4))] 
                    dataParsed["POI_code"] = results.group(4) + results.group(5)
                
            elif "core" in title:
                __class__.Logger.debug(f"Parsing {title} as a core title")
                CSA_to_bandwidth = {}
                if bandwidthFile:
                    import csv
                    with open(bandwidthFile, newline='') as r:
                        for row in csv.DictReader(r):
                            CSA_to_bandwidth[row["NBN CVC"]] = int(row["Bandwidth (Mbps)"]) * 1000000
                results = re.search(core_regex, title)
                if not results: 
                    __class__.Logger.debug(f"Parsing {title} as a core #2 title")
                    results = re.search(coreBackup_regex, title)
                    if (not results):
                        results = re.search(corelimited_regex, title)
                    dataParsed["location"] = results.group(7)
                else:
                    states = ["","","NSW", "VIC", "QLD", "SA", "WA", "TAS", "NT", "ACT"]
                    dataParsed["state"] = states[int(results.group(8))]
                    dataParsed["POI_code"] = results.group(8) + results.group(9)
                    dataParsed["location"] = results.group(10)
                    if (results.group(7)):
                        dataParsed["location"] = results.group(7) + dataParsed["location"]

                dataParsed["POI_state"] = POIstates[results.group(1)]
                dataParsed["POI_server"] = results.group(2)
                dataParsed["NBN_CVC"] = results.group(5)
                #dataParsed["connection"] = results.group(3)
                dataParsed["CSA"] = results.group(4)
                dataParsed["VLink_Circuit_ID"] = results.group(6)
                
                if bandwidthFile:
                    if dataParsed["NBN_CVC"] in CSA_to_bandwidth:
                        dataParsed["max_bandwidth"] = CSA_to_bandwidth[dataParsed["NBN_CVC"]]
            elif "swc" in title:
                __class__.Logger.debug(f"Parsing {title} as a swc title")
                results = re.search(swc_regex, title)
                dataParsed["POI_state"] = POIstates[results.group(1)]
                dataParsed["POI_server"] = results.group(2)
                dataParsed["state"] = states[int(results.group(3))]
                #dataParsed["POI_code"] = results.group(3) + results.group(4)
            else:
                __class__.Logger.warning(f"Failed Parsing {title}")
            __class__.Logger.debug(f"Title Parsed {str(dataParsed)[:300]}")
            return dataParsed
    
    async def getAllData(self, CustomParser=None, flatten=False, **kwargs) -> list[dict]:
        """_summary_

        Args:
            parseData (bool, optional): _description_. Defaults to False.
            CustomParser (function, optional): Accept a dictornary that contains; graphID, title, unit, rawData, and any other attributes set in config.yaml. Defaults to None.
            flatten (bool, optional): if CustomParser returns a list, it can be unpacked into the returning list. Defaults to False

        Returns:
            list[dict]: Returns dictionary with  graphID, title, unit, rawData, and any other attributes set in config.yaml
        """
        AllData = []               
        for graph in self.graphs:
            data = await self.getData(graph, CustomParser == None, **kwargs)

            if not type(CustomParser) == type(None):
                data = await CustomParser(data)
                if flatten:
                    AllData.extend(data)
                else:
                    AllData.append(data)
                    
            else: AllData.append(data)
        return AllData

    

    async def getData(self, graphID:int, parseData=False, parseTitles=True) -> dict:
        """Gets data for a given graphID from https://customer.ims.iseek.com.au/graph_xport.php?local_graph_id={graphID}&rra_id=5&view_type=tree

        Args:
            graphID (int): Graph ID that can be found through the url 
            parseData (bool, optional): Will the function parse the data before returning, or return the raw data. Defaults to False.

        Returns:
            dict: Returns the Title, GraphID, Unit, and Data in a dictionary
        """
        var = f"?local_graph_id={str(graphID)[:4]}&rra_id=5&view_type=tree" # Sets up url variables
        async with self.Session.post(Iseek.URL+Iseek.ACTION+var) as responce: # Sends a post to https://customer.ims.iseek.com.au/graph_xport.php?local_graph_id={graphID}&rra_id=5&view_type=tree, and recieving CSV data into variable 'responce'
            DATA_DUMP = await responce.text() #Get the raw text from the responce
            DATA_DUMP = DATA_DUMP.split("\n") #Convert each line to rows in a python list
        data = DATA_DUMP[10:-1] # Index slice off the graph properties and headings, to be left with pure data
        if parseData: # Check if parsing is needs to be done 
            data = Iseek.Parse(data) # Sends to the Parser
        Attributes = {}
        if parseTitles:
            Attributes = Iseek.Parse.title(DATA_DUMP[0].replace('"', '').replace("'", '').split(",")[1])
        return {
                    "graphid": graphID,
                    "rawTitle":DATA_DUMP[0].replace('"', '').replace("'", '').split(",")[1],
                    "unit":DATA_DUMP[1].replace('"', '').replace("'", '').split(",")[1],
                    "data": data,
                    **Attributes
                } # Returns the data

    
    async def __aexit__(self,exc_type, exc_value, traceback):
        """Used with python's 'with', therefore makes sure this script enters and closes correctly
        """
        await self.logout()
        await self.Session.__aexit__(exc_type, exc_value, traceback)


  

# Debugging/Testing Purposes
if __name__ == "__main__": 
    async def start(instance):
        async with instance as iseek:
            print(await iseek.getAllData())

    import yaml
    with open("config.yaml", "r") as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.Loader)
    Object = Iseek(cfg['Iseek']['username'],cfg['Iseek']['password'],  cfg['Iseek']['realm'], cfg['graphs'], cfg["bandwidthfile"])
    arun(start(Object))


