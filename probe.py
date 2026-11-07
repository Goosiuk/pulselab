from monitor import check_once


result = check_once("http://127.0.0.1:8088/health", timeout=2)
print(result)
