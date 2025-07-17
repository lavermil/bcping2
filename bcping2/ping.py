import os
import orjson
from pythonping import ping

HOSTS_FILE = os.path.join(os.path.dirname(__file__), "hosts.json")

def load_hosts():
    try:
        with open(HOSTS_FILE, "rb") as f:
            return orjson.loads(f.read())
    except FileNotFoundError:
        print(f"Error: File not found at '{HOSTS_FILE}'")
        #return []
        exit()
    except orjson.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in '{HOSTS_FILE}': {e}")
        #return []
        exit()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        #return []
        exit()

def save_hosts(hosts):
    with open(HOSTS_FILE, "wb") as f:
        f.write(orjson.dumps(hosts))

def check_servers(CHECK_INTERVAL):
    servers = load_hosts()
    for server in servers:
        try:
            response = ping(server["ip"], count=1, timeout=1)
            rtt = response.rtt_avg_ms
            success = response.success()
        except Exception:
            rtt = None
            success = False

        server["total_pings"] = server.get("total_pings", 0) + 1
        if success:
            server["successful_pings"] = server.get("successful_pings", 0) + 1
        else:
            server["failed_pings"] = server.get("failed_pings", 0) + 1

        server["last_rtt"] = rtt
        if rtt is not None:
            rtt_list = server.get("rtt_list", [])
            rtt_list.append(rtt)
            # Keep only the most recent 100 RTT values
            if len(rtt_list) > 100:
                rtt_list = rtt_list[-100:]
            server["rtt_list"] = rtt_list
            server["avg_rtt"] = sum(rtt_list) / len(rtt_list)

        if success == server.get("alive", False):
            server["duration"] = server.get("duration", 0) + CHECK_INTERVAL
        else:
            if server.get("attempt", 0) > 2:
                server["duration"] = 0
                server["attempt"] = 0
                server["alive"] = success
            else:
                server["attempt"] = server.get("attempt", 0) + 1

    save_hosts(servers)
