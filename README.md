# Packetpusher

Packetpusher is a network traffic generator intended to break most home networking gear. It tries to be as clever as possible to generate the most UDP traffic and give you *mostly* relevant telemetry (see example report below).

Features:
	* Asynchronous server - I hear that's hot nowadays
	* Multiprocess client that can fully utilize multi processor machines
	* Fairly decent telemetry
	* Simple


## Install

To use PacketPusher you will need:

	1. Python 2.6 or later (www.python.org)
	2. prettytable (easy_install prettytable)
	3. packetpusher.py

## Running it:

The simplest way to run packetpusher is to run both server (the receiving the generate packets) and client (the one generating the traffic) on the same machine.

To start the server, in a terminal window type:

	$ ./packetpusher.py -s
	
You should see output like this, telling you the server is running:

	[10/10/2010 22:16:17] [MainProcess] INFO: 8 cpus available, will utilize 7 processes
	[10/10/2010 22:16:17] [MainProcess] INFO: Server started on 127.0.0.1:9999

Now, to start the client and run the test, in **another** terminal window type:
	
	$ ./packetpusher.py  -c -t 60
	
You should see output like this:

	[10/10/2010 22:13:50] [MainProcess] INFO: 8 cpus available, will utilize 7 processes
	[10/10/2010 22:13:50] [MainProcess] INFO: running in client mode
	[10/10/2010 22:13:50] [MainProcess] INFO: test will run for 60 seconds
	[10/10/2010 22:13:50] [process-0] INFO: started, waiting on go-head
	[10/10/2010 22:13:50] [process-1] INFO: started, waiting on go-head
	[10/10/2010 22:13:50] [process-2] INFO: started, waiting on go-head
	[10/10/2010 22:13:50] [process-3] INFO: started, waiting on go-head
	[10/10/2010 22:13:50] [process-4] INFO: started, waiting on go-head
	[10/10/2010 22:13:50] [process-5] INFO: started, waiting on go-head
	[10/10/2010 22:13:50] [process-6] INFO: started, waiting on go-head
	[10/10/2010 22:13:55] [MainProcess] INFO: all processes started, starting test in 5 seconds...
	[10/10/2010 22:14:00] [MainProcess] INFO: test running...
	[10/10/2010 22:15:01] [process-3] INFO: network node stopped
	[10/10/2010 22:15:01] [process-4] INFO: network node stopped
	[10/10/2010 22:15:01] [process-5] INFO: network node stopped
	[10/10/2010 22:15:01] [process-0] INFO: network node stopped
	[10/10/2010 22:15:01] [process-1] INFO: network node stopped
	[10/10/2010 22:15:01] [process-6] INFO: network node stopped
	[10/10/2010 22:15:01] [process-2] INFO: network node stopped
	[10/10/2010 22:15:02] [MainProcess] INFO: test if finished, tabulating telemetry

	Results:
	+-----------+-------------+------------+-----------+-------------+------------+----------+---------+
	|   worker  | data out MB | data in MB | rate MB/s | packets out | packets in | packet/s | seconds |
	+-----------+-------------+------------+-----------+-------------+------------+----------+---------+
	| process-0 |    2099.0   |    0.0     |   34.69   |  2150045.0  |    0.0     | 35523.02 | 60.5254 |
	| process-1 |    2104.0   |    0.0     |   34.75   |  2155157.0  |    0.0     | 35582.14 | 60.5685 |
	| process-2 |    2099.0   |    0.0     |   34.59   |  2150045.0  |    0.0     | 35421.37 | 60.6991 |
	| process-3 |    2148.0   |    0.0     |   35.38   |  2200362.0  |    0.0     | 36224.96 | 60.7416 |
	| process-4 |    2099.0   |    0.0     |   34.47   |  2150045.0  |    0.0     | 35298.43 | 60.9105 |
	| process-5 |    2151.0   |    0.0     |   35.23   |  2203223.0  |    0.0     | 36071.22 | 61.0798 |
	| process-6 |    2152.0   |    0.0     |   35.16   |  2204603.0  |    0.0     | 36002.45 | 61.2348 |
	|   total   |   14856.91  |    0.0     |   242.62  |  15213480.0 |    0.0     | 248444.6 | 61.2349 |
	+-----------+-------------+------------+-----------+-------------+------------+----------+---------+
	$ 
	
In the example above, we told packetpusher to run a "timed run" for 60 seconds (the -t flag). Packetpusher automatically calculated the best way to utilize the client's CPU and displayed all the telemetry goodness (in the example above we hit 242 MB/s of throughput)
	

## Feedback
Send your hatemail to raf@ophion.org	
