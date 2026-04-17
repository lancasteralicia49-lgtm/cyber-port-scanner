import socket
import threading
from datetime import datetime
import csv

print("-" * 50)

# User input
target = input("Enter target IP: ")
start_port = int(input("Start port: "))
end_port = int(input("End port: "))

print(f"\nScanning target: {target}")
print(f"Port range: {start_port} - {end_port}")
print(f"Time started: {datetime.now()}")
print("-" * 50)

# Thread control
MAX_THREADS = 100
semaphore = threading.Semaphore(MAX_THREADS)

lock = threading.Lock()
results = []

def scan_port(port):
    semaphore.acquire()

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket.setdefaulttimeout(0.5)

        result = s.connect_ex((target, port))

        if result == 0:
            try:
                service = socket.getservbyport(port)
            except:
                service = "unknown"

            try:
                banner = s.recv(1024).decode().strip()
            except:
                banner = "No banner"

            with lock:
                print(f"[+] Port {port} OPEN | {service} | {banner}")
                results.append([port, service, banner])

        s.close()

    finally:
        semaphore.release()

threads = []

for port in range(start_port, end_port + 1):
    t = threading.Thread(target=scan_port, args=(port,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

# Save to CSV
filename = f"scan_{target}.csv"

with open(filename, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Port", "Service", "Banner"])
    writer.writerows(results)

print("-" * 50)
print("Scan complete.")
print(f"Results saved to {filename}")
print("-" * 50)
