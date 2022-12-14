from scrapper import Iseek
from asyncio import run as arun
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS


class InfluxClient:
    def __init__(self,url,token,org,bucket,graphs=[]): 
        self._org=org 
        self._bucket = bucket
        self._client = InfluxDBClient(url=url, token=token)
    
    def write_data(self,data,write_option=SYNCHRONOUS):
        write_api = self._client.write_api(write_option)
        write_api.write(self._bucket, self._org , data,write_precision='s')
    
    async def start(self, instance):
        from time import sleep
        while True:
            async with instance:
                data = await instance.getAllData(self.InfluxDataParse, True, bandwidth="./bandwidth.csv")
                self.write_data(data,write_option=ASYNCHRONOUS)
            print("data")
            sleep(60*5)
            

    def GetLastTimestamp(self, graphID):
        query = f'from(bucket: "{self._bucket}")\
        |> range(start: -12h)\
        |> filter(fn: (r) => r.graphID == "{graphID}")\
        |> sort(columns: ["_time"])\
        |> last()'
        query_api = self._client.query_api()
        result = query_api.query(org=self._org, query=query)
        timeThreshold = 0
        if len(result):
            timeThreshold = result[0].records[0].get_time().timestamp()
        return timeThreshold

    def InfluxDataParse(self, dataSet):
        influxArray = []
        timeThreshold = self.GetLastTimestamp(dataSet["graphid"])
        tags = dataSet.copy()
        del tags["data"], tags["unit"]
        previousOutbound = sum(Iseek.ParseRow(dataSet["data"][0])[1:3])
        for data in dataSet["data"]:
            time, inbound, outbound = Iseek.ParseRow(data)
            bandwidthRoC = ((inbound+outbound)-previousOutbound) / (60*5) 
            if timeThreshold < time:
                influxArray.append({
                    "measurement": dataSet["unit"],
                    "tags": tags,
                    "fields": {"inbound": inbound,"outbound": outbound, "bandwidth": (inbound+outbound) },
                    "time": time
                })
                influxArray.append({
                    "measurement": "bits/s^2",
                    "tags": tags,
                    "fields": {"bandwidthRoC": bandwidthRoC },
                    "time": time
                })
            previousOutbound = (inbound+outbound)
        return influxArray
            
            

if __name__ == "__main__":
    import yaml
    with open("config.yaml", "r") as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.Loader)
    Object = Iseek(cfg['Iseek']['username'],cfg['Iseek']['password'],  cfg['Iseek']['realm'], cfg["graphs"])

    IC = InfluxClient(cfg["InfluxDB"]["url"],cfg["InfluxDB"]["token"],cfg["InfluxDB"]['org'],cfg["InfluxDB"]['bucket'])

    arun(IC.start(Object))