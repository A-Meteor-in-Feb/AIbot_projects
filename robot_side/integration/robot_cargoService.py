import time
import requests

class SimpleTTLCache:
    """
        A simple TTL cache: key→(cargo_info, timestamp) in store
        For multiple robots, key = (robotId, binId)
        For the whole inventory, key = robotId
        For now, I am not sure whether the bins are managed by all robots or differnt robots corresponds to the different bin.
    """
    def __init__(self, ttl_seconds):
        """
            Initiation of the TTL cache.
            parameters:
                ttl_seconds: Time-To-Live for every record in the cache, int type.
        """
        self.ttl = ttl_seconds
        self.store = {}


    def get(self, key):
        """
            get the record from the cache.
            key: (robotId, binId) for the specific binId
            key: robotId for the whole inventory
        """
        record = self.store.get(key)
        if not record:
            return None
        cargo_info, timestamp = record
        if time.time() - timestamp > self.ttl:
            del self.store[key]
            return None
        return cargo_info


    def set(self, key, cargo_info):
        """
            Set the cargo info.
            parameters:
                key: the key used to mark the cargo_info
                cargo_info: specific details for the record.
        """
        self.store[key] = (cargo_info, time.time())


class CargoService:
    def __init__(self, backend_base_url, backup_bin, backup_inventory):
        """
            Parameters:
                backend_base_url: the url used to search for the cargo info, type: str.
                backup_bin: when you cannot get the real-time data, use the backup info, type: dict.
                backup_inventory: when you cannot get the real-time data, use the backup info, type: dict.
        """
        self.backend = backend_base_url
        #set the default ttl as 5 minutes.
        self.bin_cache = SimpleTTLCache(ttl_seconds=300)
        #set the default ttl as 5 minutes.
        self.inventory_cache = SimpleTTLCache(ttl_seconds=300)
        self.backup_bin = backup_bin
        self.backup_inventory = backup_inventory


    def fetch_from_backend(self, path, params):
        """
            parameters:
                path: 1) /api/JKROBOT/<string:robotId>/cargo 
                      2) /api/JKROBOT/<string:robotId>/cargo/inventory
                params:
        """
        url = f"{self.backend}{path}"
        try:
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

    def get_bin(self, robotId, binId) -> dict:
        """
            Get the specific bin info.
            Parameters:
                robot_id: the robot's id, type: str.
                bin_id: the bin's id, type: int.
            Return: A dict which has detailed info of the bin.
        """
        key = (robotId, binId)
        
        # 1 - try to get info from the cache.
        cached = self.bin_cache.get(key)
        if cached:
            return cached

        # 2 - try to get the info by the RESTful API
        data = self.fetch_from_backend(
            path = f"/api/JKROBOT/{robotId}/cargo",
            parameters = {"robotId": robotId, "binId": binId}
        )

        if data and data.get("cargo") is not None:
            cargo = data["cargo"]
            self.bin_cache.set(key, cargo)
            return cargo

        # 3 - return backup info
        return self.fallback_bin


    def get_inventory(self, robotId) -> dict:
        """
            Get the specific inventory's info.
            Parameters:
                robot_id: the robot's id, type: str.
            Return: A dict which has detailed info of the inventory.
        """
        key = robotId

        # 1 - try to get info from the cache.
        cached = self.inventory_cache.get(key)
        if cached:
            return cached

        # 2 - try to get the info by the RESTful API
        data = self._fetch_from_backend(
            path = f"/api/JKROBOT/{robotId}/cargo/inventory",
            params = {"robotId": robotId}
        )

        if data and data.get("inventory") is not None:
            inventory = data["inventory"]
            self.inventory_cache.set(key, inventory)
            return inventory

        # 3 - return backup info
        return self.fallback_inventory
