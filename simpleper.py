
import argparse
import socket     # Import the socket module to enable network communication
import time  # Import the time module to measure time intervals
import threading  # Import the threading module for concurrent execution
import sys  # Import the sys module for system-related operations

BUFFER_SIZE = 1000
# Dictionary to convert bytes to different formats (B, KB, MB)
bytesDict = {'B': 1, 'KB': 1000, 'MB': 1000000}

# Function to parse command line arguments


def parse_args():
    # Define an ArgumentParser object with a description of the arguments
    parser = argparse.ArgumentParser(description='simpleperf arguments')
    parser.add_argument('-s', '--server', action='store_true',
                        help='enable the server mode')  # Add the -s or --server option to enable server mode
    parser.add_argument('-c', '--client', action='store_true',
                        help='enable the client mode')  # Add the -c or --client option to enable client mode
    parser.add_argument('-b', '--bind', default='127.0.0.1',
                        help='allows to select the ip address of the server’s interface where the client should connect')  # Add the -b or --bind option to select the IP address of the server's interface
    parser.add_argument('-I', '--serverAddr', default='127.0.0.1',
                        help='address of the server to connect to (required in client mode)')  # Add the -I or --serverAddr option to specify the server address
    parser.add_argument('-p', '--port', type=int, default=12000,
                        help='allows to use select port number on which the server should listen')  # Add the -p or --port option to specify the server's port number
    parser.add_argument('-f', '--format', choices=['B', 'KB', 'MB'], default='MB', help='to choose the format of the summary of results'
                        )  # Add the -f or --format option to specify the format of the results
    parser.add_argument('-P', '--parallel', type=int, default=1,
                        help='Number of parallel connections')  # Add the -P or --parallel option to specify the number of parallel connections to use during the transfer
    parser.add_argument('-t', '--time', type=int, default=25,
                        help='the total duration in seconds')  # Add the -t or --time option to specify the total duration of the operation in seconds
    parser.add_argument('-n', '--num', type=str,
                        help='Transfer number of bytes')  # Add the -n or --num option to specify the number of bytes
    parser.add_argument('-i', '--interval', type=int, default=1,
                        help='Interval for statistics')  # Add the -i or --interval option to specify the interval at which should be collected during the transfer
    # Parse the command-line arguments and store them in an object called "args"
    args = parser.parse_args()
    if args.format:  # If the -f or --format option was used
        # Check if the unit of the input value is valid
        if args.format not in ['B', 'KB', 'MB']:
            # Raise an error if the unit is invalid
            parser.error("the unit Should be B, KB, MB.")
    if args.interval <= 0:  # If the -i or --interval option is less than or equal to 0
        # an error
        parser.error("Interval has a wrong values.")
    if not args.client and not args.server:
        parser.error('One of the client or the server is required.')
    return args  # Return the parsed arguments object

    # Function to print the results after data transfer


def print_summary(serverAddr, total_bytes, transfer_time, format):
    # Convert the size to the desired format and round to two decimal
    transfer_amount = round(total_bytes / bytesDict[format], 2)
    # Round the time to two decimal
    elapsed_time = round(transfer_time, 2)
    # Calculate the transfer rate in Mbps and round to two decimal
    if (elapsed_time > 0):
        transfer_rate = round(
            total_bytes * 8 / (elapsed_time * bytesDict[format]), 2)
        # Print the results
        print(
            f"{serverAddr}\t[0.0 - {elapsed_time}]\t{transfer_amount}\t{transfer_rate} {format}ps")
    else:
        print("the transfer_time is zero")

# Function to run the server


def server(args):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Bind the server to a specific address and port
        s.bind((args.bind, args.port))
        # Start listening
        s.listen(10)
        # Print the server header
        print("---------------------------------------------")
        print(f"A simpleperf server is listening on port {args.port}")
        print("---------------------------------------------")

        while True:  # Loop indefinitely
            conn, addr = s.accept()  # Accept a new client connection
            # Start a new thread
            threading.Thread(target=start_connection,
                             args=(conn, addr, args)).start()


def start_connection(conn, addr, args):
    with conn:
        print("---------------------------------------------")
        print(
            f"A simpleperf client connecting to server  {args.serverAddr}, port {args.port}")
        # Print the client header
        print("---------------------------------------------")
        total_bytes = 0  # the total number of bytes received
        start_time = time.time()  # Start the clock to measure the time it takes to receive data
        while True:
            data = conn.recv(BUFFER_SIZE)  # Receive data from the client
            if "BYE" in data.decode():  # If no data is received, break the loop
                break
            total_bytes += len(data)  # Increase the number of bytes received
        # Stop the clock and calculate the time it took to receive the data
        elapsed_time = time.time() - start_time
        # Send a confirmation that all data has been received
        conn.sendall(b"ACK: BYE")
        conn.close()  # stop the connection to the client
        print(f"ID\tInterval\tReceived\tRate")  # Print results
        print_summary(addr, total_bytes, elapsed_time, args.format)
# Function to initiate the client mode


def client(args):
    # Create a TCP socket object
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as c:
        # Connect to the server
        try:
            c.connect((args.serverAddr, args.port))
        except ConnectionRefusedError:
            print("Error: Connection refused. Make sure the server is running and the IP address and port are correct.")
            sys.exit(1)
        # Print the client header
        print("---------------------------------------------")
        print(
            f"A simpleperf client connecting to server  {args.serverAddr}, port {c.getsockname()}")
        print("---------------------------------------------")
        print(f"ID\tInterval\tTransferred\tRate")  # Print results
        # Start the timer
        start_time = time.time()
        # the total number of bytes sent
        total_bytes = 0
        # Check if -n flag is provided
        if args.num:
            num_bytes = args.num
            numbers = ''
            letters = ''
            for i in num_bytes:
                if i.isdigit():
                    numbers += i
                else:
                    letters += i
            get_format = letters.upper()
            if (get_format == 'B'):
                format = 'B'
            elif (get_format == 'K' or get_format == 'KB'):
                format = 'KB'
            elif (get_format == 'M' or get_format == 'MB'):
                format = 'MB'
            else:
                print('The format is not difined')
                sys.exit()
            # Convert input string to bytes
            num_bytes = bytesDict[format] * int(numbers)
            while total_bytes < num_bytes:
                # Generate some random data
                data = bytes(BUFFER_SIZE)
                # Send data in chunks of 1000 bytes
                c.sendall(data)
                total_bytes += len(data)
        elif args.interval:
            limit_time = args.time
            # Loop to send data
            interval = args.interval
            # the limited time for evry intervals
            interval_time = int(limit_time // interval)
            for i in range(interval):
                start_interval = i * interval_time
                end_interval = min((i + 1) * interval_time, limit_time)
                interval_bytes = 0
                while True:
                    if (time.time()-start_time >= end_interval):
                        break
                    # Generate some random data
                    data = bytes(BUFFER_SIZE)
                    # Send the data
                    c.sendall(data)
                    # Receive the response from the server and Convert the size to the desired format and round to two decimal places
                    total_bytes += len(data)
                    interval_bytes += len(data)
                format = args.format
                transfer_amount = round(interval_bytes / bytesDict[format], 2)
                # Calculate the transfer rate and round to two decimal numbers
                transfer_rate = round(total_bytes * 8 / (end_interval - start_interval) /
                                      bytesDict[format], 2)
                if interval > 1:
                    # Print the results of the intervals
                    print(
                        f"{c.getsockname()}\t[{start_interval} - {end_interval}]\t{transfer_amount}\t{transfer_rate} {format}ps")

        # Send finish message to server
        c.send(b"BYE")
        # Check if the response is a BYE message or not
        response = c.recv(BUFFER_SIZE)
        if response != b"ACK: BYE":
            print("Error: Did not receive acknowledgement from server")
            # Close client socket
            c.close()
            return
        # Calculate and print total transfer time and bandwidth summary
        end_time = time.time()
        transfer_time = end_time - start_time
        if args.interval > 1:
            print("---------------------------------------------")
        print_summary(c.getsockname(), total_bytes, transfer_time, format)
        # Close and stop client socket
        c.close()


def start_threading(args):
    # Open the specified number of connections in parallel
    threads = []
    for i in range(args.parallel):
        t = threading.Thread(target=client, args=(args,))
        t.start()
        threads.append(t)

    # Wait for all threads
    for t in threads:
        t.join()


def main():
    args = parse_args()
    # Run the program in client or server mode, depending on the arguments which given.
    if args.client:
        start_threading(args)

    elif args.server:
        server(args)


if __name__ == '__main__':
    main()
