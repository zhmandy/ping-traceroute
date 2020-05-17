# Simple Proxy Server

📠Networking diagnostic tools (ping & traceroute) in Python

The tools are implemented with ICMP messages and raw sockets. It sends ICMP echo to destination and processes ICMP reply message or error message. It prints info (IP address, RTT) along the route path.

## Usage

>  python3 .\IcmpPing.py [website]
>
>  python3 .\Traceroute.py [website]

## Sample Output

### ping

![](samples/ping-1.png)

### traceroute

![](samples/tr-1.png)

## License

MIT License
