# Nmap Ping Scan (`-sn`) - Network Discovery

## Objective
To identify live hosts in the local network (192.168.1.0/24) using ICMP Echo Requests.

## Command Used

nmap -sn 192.168.1.0/24


## Result Summary
- 5 hosts were found to be up.
- Discovered IP and MAC addresses.
- Common vendors identified (e.g., Intel, Epson, etc.).

## Sample Output
Host is up (0.0023s latency).                                                                                                                                                                         
MAC Address: 74:24:9F:DF:6D:F7 (Tibro)   


## Use Case
Useful for discovering active devices in a subnet, such as printers, phones, and laptops.
