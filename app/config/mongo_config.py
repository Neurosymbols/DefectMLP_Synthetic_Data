from pymongo import MongoClient

conn_string = "mongodb://localhost:27017/"
client  = MongoClient(conn_string)
db = client["pcb_synthetic_data"]