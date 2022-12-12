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


    def __init__(self, username:str, password:str, realm:str, graphs={}) -> None:
        """Initizes the Iseek Scrapper Class, with nessary values to complete tasks 

        Args:
            username (str): Iseek Account Username
            password (str): Iseek Account Password
            realm (str): Which ever service the Iseek Account is connected to, local or LDAP
            graphs (dict, optional): Accept a dictornary with the key being graphID, and value being a dictornary of attibutes ie. {2380: {'state': 'QLD', 'suburb': 'N/A'}}. Defaults to {}.
        """
        self.username = username
        self.password = password
        self.realm = realm
        self.graphs = graphs

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
        await self.Session.post(Iseek.URL+Iseek.LOGOUT)


    def ParseData(DATA_DUMP:list[str], timeThreshold=0) -> list[tuple]:
        """Loops through that data, parsing it to a state that is easy to use

        Args:
            DATA_DUMP (list[str]): list of data, received from getData 
            timeThreshold (int, optional): Timestamp (in Unix time) of the last entry into the database, so that those, and later entries are skipped. Defaults to 0.

        Returns:
            list[tuple]: Returns a list containing tuple with a structure of (timestamp, inbound, outbound). Timestamp is formatted in Unix time
        """
        Parsed_Data = []
        for data in DATA_DUMP:
            data = data.replace('"', '').split(",")
            time = int(datetime.timestamp(Iseek.TimeZone.localize(datetime.strptime(data[0],"%Y-%m-%d %H:%M:%S"))))
            if timeThreshold < time:
                Parsed_Data.append((time, float(data[1]), float(data[2])))
        return Parsed_Data
    
    async def getAllData(self, parseData=False) -> list[dict]:
        """_summary_

        Args:
            parseData (bool, optional): _description_. Defaults to False.

        Returns:
            list[dict]: _description_
        """
        return 
    
    async def getData(self, graphID:int, parseData=False) -> dict:
        """Gets data for a given graphID from https://customer.ims.iseek.com.au/graph_xport.php?local_graph_id={graphID}&rra_id=5&view_type=tree

        Args:
            graphID (int): Graph ID that can be found through the url 
            parseData (bool, optional): Will the function parse the data before returning, or return the raw data. Defaults to False.

        Returns:
            dict: Returns the Title, GraphID, Unit, and Data in a dictionary
        """
        var = f"?local_graph_id={graphID}&rra_id=5&view_type=tree" # Sets up url variables
        async with self.Session.post(Iseek.URL+Iseek.ACTION+var) as responce: # Sends a post to https://customer.ims.iseek.com.au/graph_xport.php?local_graph_id={graphID}&rra_id=5&view_type=tree, and recieving CSV data into variable 'responce'
            DATA_DUMP = await responce.text() #Get the raw text from the responce
            DATA_DUMP = DATA_DUMP.split("\n") #Convert each line to rows in a python list
        data = DATA_DUMP[10:-1] # Index slice off the graph properties and headings, to be left with pure data
        if parseData: # Check if parsing is needs to be done 
            data = Iseek.ParseData(data) # Sends to the Parser

        return {
                    "GraphID": graphID,
                    "Title": DATA_DUMP[0].replace('"', '').replace("'", '').split(",")[1], 
                    "Unit":DATA_DUMP[1].replace('"', '').replace("'", '').split(",")[1],
                    "Data": data
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
            print(await iseek.getData())  

    import yaml
    with open("config.yaml", "r") as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.Loader)
    Object = Iseek(cfg['Iseek']['username'],cfg['Iseek']['password'],  cfg['Iseek']['realm'], cfg['graphs'])
    print(cfg['graphs'])
    arun(start(Object))


