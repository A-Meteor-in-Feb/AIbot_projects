import time

class TTLCache:
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
    def __init__(self, backup_bin, backup_inventory):
        """
            Parameters:
                backend_base_url: the url used to search for the cargo info, type: str.
                backup_bin: when you cannot get the real-time data, use the backup info, type: dict.
                backup_inventory: when you cannot get the real-time data, use the backup info, type: dict.
        """
        #set the default ttl as 5 minutes.
        self.bin_cache = TTLCache(ttl_seconds=300)
        #set the default ttl as 5 minutes.
        self.inventory_cache = TTLCache(ttl_seconds=300)
        self.backup_bin = backup_bin
        self.backup_inventory = backup_inventory


    def get_bin_cache(self, robotId, binId):
        """
            Get specific bin info from the cache.
            Parameters:
                robot_id: the robot's id, type: str.
                bin_id: the bin's id, type: int.
            Return: A dict which has detailed info of the bin.
        """
        key = (robotId, binId)
        
        cached = self.bin_cache.get(key)
        if cached:
            return cached
        else:
            return None


    def get_bin_backup(self):
        """
            Return backup info of the bin
        """
        return self.backup_bin


    def get_inventory_cache(self, robotId):
        """
            Get the specific inventory's info from cache.
            Parameters:
                robot_id: the robot's id, type: str.
            Return: A dict which has detailed info of the inventory.
        """
        key = robotId

        cached = self.inventory_cache.get(key)
        if cached:
            return cached
        else:
            return None
        
    def get_inventory_backup(self):
        """
            Return backup info of the inventory
        """
        return self.backup_inventory
    
    def set_cargo_bin_info(self, robotId, binId, info):
        """
            Set the cargo info into the cache
        """
        self.bin_cache.set(key=(robotId, binId), cargo_info=info)

    def set_inventory_info(self, robotId, info):
        """
            Set the inventory info into the cache
        """
        self.inventory_cache.set(key=robotId, cargo_info=info)
