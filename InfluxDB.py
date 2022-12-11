import scrapper
from asyncio import run as arun
import influxdb_client, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS


class InfluxClient:
    def __init__(self,token,org,bucket,graphs=[]): 
        self._org=org 
        self._bucket = bucket
        self._client = InfluxDBClient(url="http://192.168.100.151:8086", token=token)
    
    def write_data(self,data,write_option=SYNCHRONOUS):
        write_api = self._client.write_api(write_option)
        write_api.write(self._bucket, self._org , data,write_precision='s')

    def query_data(self,query):
        query_api = self._client.query_api()
        result = query_api.query(org=self._org, query=query)
        print(result)
        results = []
        for table in result:
            for record in table.records:
                results.append((record.get_value(), record.get_field()))
        print(results)
        return results
    
    async def start(self, instance):
        print(instance.graphs)
        async with instance:
            await Object.login()
            for id in instance.graphs:
                data = self.InfluxDataParse(id, instance.graphs[id]["state"],  instance.graphs[id]["suburb"], *(await Object.getData(id)))
                self.write_data(data,write_option=ASYNCHRONOUS)

    def InfluxDataParse(self, graphID, state, suburb, title, rawData):
        influxArray = []
        query = f'from(bucket: "{self._bucket}")\
        |> range(start: -12h)\
        |> filter(fn: (r) => r.graphID == "{graphID}")\
        |> sort(columns: ["_time"])\
        |> last()'
        query_api = self._client.query_api()
        result = query_api.query(org=self._org, query=query)
        timeOffset = 0
        if len(result):
            timeOffset = result[0].records[0].get_time().timestamp()
        
        DataSET = scrapper.Iseek.ParseData(rawData, timeOffset)
        print(DataSET)
        for item in DataSET:
            influxArray.append({
            "measurement": "b/s",
            "tags": {"title": title, "graphID": graphID, "State": state, "Suburb": suburb},
            "fields": {"inbound": item[1],"outbound": item[2]},
            "time": item[0]
            })
        return influxArray
            

if __name__ == "__main__":
    import yaml
    with open("config.yaml", "r") as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.Loader)
    Object = scrapper.Iseek(cfg['Iseek']['username'],cfg['Iseek']['password'],  cfg['Iseek']['realm'], cfg["graphs"])
    token="Tks10ZxZQsbC-1bHVY3mBcLiOUu06DELhOpJ5PfS8VrCfoLg2Nst7IUE0COlR-3k_z7FJIOTjaoma-BL_umsCg=="

    org = "vonex"
    bucket = "iseek"

    IC = InfluxClient(token,org,bucket)

    arun(IC.start(Object))