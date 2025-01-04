import requests
import time
import sys
import logging
import coloredlogs
import argparse
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Config:
    def __init__(self, base_url, api_key, use_proxy, proxy_address, proxy_port, max_task):
        self.base_url = base_url
        self.api_key = api_key
        self.use_proxy = use_proxy
        self.proxy_address = proxy_address
        self.proxy_port = proxy_port
        self.max_task = max_task

config = Config(
    base_url="https://127.0.0.1:3443/api/v1",
    api_key="1986ad8c0a5b3df4d7028d5f3c06e936cceae7f7bab514c58aa50e59e95d15d81",
    use_proxy=True,
    proxy_address="192.168.31.1",
    proxy_port=10809,
    max_task=15
)

requset_header = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "X-Auth": config.api_key
}

logger = logging.getLogger("awvs_buddy")
coloredlogs.install(
    level=logging.INFO,
    logger=logger,
    fmt="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class Target:
    def __init__(self):
        pass
    
    def add_target(self, address):
        request_data = {
            "address": address,
            "description": "",
            "type": "default",
            "criticality": 30
        }
        response = requests.post(config.base_url + '/targets', headers=requset_header, json=request_data, verify=False)
        if response.status_code == 201:
            response_data = response.json()
            target_id = response_data.get('target_id')
            if target_id:
                return target_id
        else:
            return "error"

        
    def target_config(self, target_id):
        request_data = {
            "description": "Target configuration default values",
            "limit_crawler_scope": True,
            "login": {
            "kind": "none"
            },
            "sensor": False,
            "ssh_credentials": {
            "kind": "none"
            },
            "proxy": {
            "enabled": False
            },
            "authentication": {
            "enabled": False
            },
            "client_certificate_password": "",
            "scan_speed": "slow",
            "case_sensitive": "auto",
            "proxy": {
                "enabled": config.use_proxy,
                "protocol": "http",
                "address": config.proxy_address,
                "port": config.proxy_port
                },
            "technologies": [],
            "custom_headers": [],
            "custom_cookies": [],
            "excluded_paths": [],
            "user_agent": "",
            "debug": False
        }
        requests.delete(config.base_url + f'/targets/{target_id}/configuration/client_certificate', verify=False)
        response = requests.patch(config.base_url + f'/targets/{target_id}/configuration', headers=requset_header, json=request_data, verify=False)
        if response.status_code == 204:
            return True
        return False
    
    
class Scan:
    def __init__(self):
        pass
    
    
    def get_scans_status(self):
        response = requests.get(config.base_url + f'/scans?q=status:processing', headers=requset_header, verify=False)
        pagination = response.json().get("pagination")
        processing_count = pagination["count"]
        return processing_count > config.max_task
    
    
    def scan_target(self, target_id):
        request_data = {
            "target_id": target_id,
            "profile_id": "11111111-1111-1111-1111-111111111111",
            "schedule": {
            "disable": False,
                "start_date": None,
                "time_sensitive": False
            }
        }
        response = requests.post(config.base_url + '/scans', headers=requset_header, json=request_data, verify=False)
        if response.status_code == 201:
            return True
        else:
            return False
        
    
    def start_scan(self, url):
        target = Target()
        if self.get_scans_status():
            logger.info(f"The number of tasks being scanned has reached {config.max_task}. Try again in 5 minutes ...")
            time.sleep(60 * 5)
            return False
        
        target_id = target.add_target(url)
        if target_id == "error":
            return False
        is_config = target.target_config(target_id=target_id)
        if not is_config:
            return False
        is_scanning = self.scan_target(target_id=target_id)
        return is_scanning
               
    

def main():
    parser = argparse.ArgumentParser(
        description="awvs api tools",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-l', '--file', help='File path to read', required=False)
    parser.add_argument('-u', '--url', help='URL to process', required=False)

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    if args.file and args.url:
        logger.error("Error: You cannot provide both -l (file) and -u (URL) at the same time.")
    else:
        scan = Scan()
        if args.file:
            with open(args.file, "r") as file:
                for line in file:
                    line = line.strip()
                    is_scan = scan.start_scan(line)
                    if is_scan:
                        logger.info(f"Target {line} start scanning ...")
        if args.url:
            is_scan =scan.start_scan(args.url)
            if is_scan:
                logger.info(f"Target {args.url} start scanning ...")
                    
            
    logger.info("Done.")


if __name__ == "__main__":
    main()