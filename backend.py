import os
import time
import queue
import numpy as np
import pandas as pd
from datetime import datetime

class DiagnosticParser:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        
    def parse_files(self, log_queue):
        log_queue.put({"message": f"Mapping directory: '{self.folder_path}'...", "level": "info", "time": datetime.now().strftime("%H:%M:%S")})
        time.sleep(0.3)
        
        if not os.path.exists(self.folder_path):
            log_queue.put({"message": f"Path '{self.folder_path}' missing or inaccessible.", "level": "error", "time": datetime.now().strftime("%H:%M:%S")})
            raise FileNotFoundError()
            
        simulated_files = [f"log_{i}.txt" for i in range(1, 6)]
        
        dtc_pool = {
            'P0101': 'MAF Sensor Range/Perf', 'P0300': 'Misfire Detected', 
            'P0420': 'Catalyst Efficiency Low', 'P0171': 'System Too Lean',
            'P0700': 'TCM Malfunction', 'U0100': 'ECM Comm Lost'
        }
        models = ['Model S', 'Model X', 'Truck A', 'Sedan Eco']
        modules = ['ECM (Engine)', 'TCM (Transmission)', 'BCM (Body)', 'ABS Module']
        statuses = ['Open', 'In Progress', 'Resolved', 'Under Investigation']
        
        # Synthetic VIN component generation pools
        vin_suffixes = [f"{np.random.randint(100000, 999999)}" for _ in range(30)]
        
        rows = []
        for file in simulated_files:
            for _ in range(np.random.randint(20, 40)):
                chosen_code = np.random.choice(list(dtc_pool.keys()))
                chosen_model = np.random.choice(models)
                # Formulate a pseudo-VIN based on Model selection
                vin_prefix = chosen_model.replace(" ", "").upper()[:4]
                chosen_vin = f"1YV1BR8A{vin_prefix}{np.random.choice(vin_suffixes)}"
                
                rows.append({
                    "File Name": file, 
                    "Module": np.random.choice(modules),
                    "Code": chosen_code, 
                    "Description": dtc_pool[chosen_code],
                    "Status": np.random.choice(statuses), 
                    "Comments": "Auto-logged anomaly profile.",
                    "Reviewer": "Admin", 
                    "Vehicle Model Name": chosen_model,
                    "Vehicle VIN": chosen_vin,
                    "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
        return pd.DataFrame(rows)

def background_worker(folder_path, log_queue, result_container):
    try:
        parser = DiagnosticParser(folder_path)
        result_container['dataframe'] = parser.parse_files(log_queue)
        result_container['status'] = 'done'
    except Exception:
        result_container['status'] = 'error'