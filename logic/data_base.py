import os
from supabase import create_client, Client
from dotenv import load_dotenv
from logic.functions import GetGameFolder

class Database:
    def __init__(self):
        load_dotenv(GetGameFolder() + "/.env")
        self.database_url = os.getenv("DATABASE_URL")
        self.database_password = os.getenv("DATABASE_PASSWORD")
        
        self.supabase: Client = create_client(self.database_url, self.database_password)

    def GetTable(self, table_name):
        responce = (
            self.supabase.table(table_name)
            .select("*")
            .csv()
            .execute()
        )
        return responce.data

    def InsertData(self, table_name, data):
        table = self.GetTable(table_name)
        print(table)
        try:
            for idx, data in enumerate(table):
                if idx > 0:
                    print(data)
                    if data:
                        response = (
                            self.supabase.table(table_name)
                            .update({"player2": data})
                            .eq("id", data["id"])
                            .execute()
                        )
                        return
        except Exception as e:
            print(e)
        response = (
            self.supabase.table(table_name)
            .insert({"player1": data})
            .execute()
        )