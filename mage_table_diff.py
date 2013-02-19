#!/usr/bin/env python

################################################################################
## NAME: MAGENTO SKU TO ENTITY_ID CONVERTER - Version 0.0.1
## AUTHOR: Jason R Alexander
## INFO: This script will take a csv file with sku and map out their entity_ids in a new csv file
#################################################################################

import sys
import os
import oursql
import string
import time
import base64
import csv
import datetime
from urllib import urlopen
import logging
import glob
import traceback
import ast
import resource




class mageTableDiff(object):
	"""Diff two csv files """
	# --------------------------------------------------------------------------------------------------------------------------------------------------------------- #
	def __init__(self, config_file):
		#Get the name of the script
		self.appName = str(os.path.splitext(os.path.basename(__file__))[0])
		#Let's spot check out replace progress
		#Check for required config file
		check_file_path = os.path.exists(config_file)
		if(check_file_path):    
			#Read config file
			reader = csv.reader(open(config_file, "rb"))	    
			for row in reader:
				configValues = row[0].split(':')
				if(configValues[0] == 'COMPARE_CSV_ONE'):
					self.compareCSVOne= configValues[1]
				if(configValues[0] == 'COMPARE_CSV_TWO'):
					self.compareCSVTwo = configValues[1]
				if(configValues[0] == 'EMAIL'):
					self.email = configValues[1]
				if(configValues[0] == 'LOG'):
					self.logFile = configValues[1]
					#Let's remove old log and csv files at the end here. 
					self.removeOldFile(self.logFile)

		else:
			sys.exit('mageSkuToEntityId -- ERROR: Please provide configuration file!!')

	    
	# --------------------------------------------------------------------------------------------------------------------------------------------------------------- #
	def scriptInfo(self):
		"""This just displays script information """
		memory_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
		self.log("The script " + str(self.appName) + " was ran at " + str(datetime.datetime.now()))
		self.log("Using log file: " + str(self.logFile))
		self.log("Script memory usage: "+ str(memory_usage) +"kb")


	# --------------------------------------------------------------------------------------------------------------------------------------------------------------- #
	def dbConnect(self):
		"""Basic sql connect which creates a cursor to execute queries """
		#try first host
		try:
			conn = oursql.connect(host = self.dbHost1, user=self.dbUsername, passwd=self.dbPassword,db=self.database, use_unicode=False, charset=None, port=3306)
		#if no first host, try second host
		except:
			conn = oursql.connect(host = self.dbHost2, user=self.dbUsername, passwd=self.dbPassword,db=self.database, use_unicode=False, charset=None, port=3306)		
		curs = conn.cursor(oursql.DictCursor)
		curs = conn.cursor(try_plain_query=False)

		return curs

	# --------------------------------------------------------------------------------------------------------------------------------------------------------------- #
	def log(self, message):
		"""This is used to write log files """
		logging.basicConfig(
			filename=self.logFile,
			format='%(asctime)-6s: %(name)s - %(levelname)s - %(message)s')
		logger = logging.getLogger(self.appName)
		logger.setLevel(logging.INFO)
		logger.info(message)

	# --------------------------------------------------------------------------------------------------------------------------------------------------------------- #
	def removeOldFile(self, filepath):
		"""Checks to see if a file exists """
		fileExists = os.path.exists(filepath)
		if(fileExists == True):
			os.remove(filepath)
			file_create = open(filepath, 'w')
			file_create.write('')
			file_create.close()			
			reponse = '  -->  Deleting old file and recreating'
		else:
			#Create a blank file.
			file_create = open(filepath, 'w')
			file_create.write('')
			file_create.close()
			reponse = '  --> Creating new file'
		
		message = "FILE: " + filepath + reponse
		self.log(message)
		print message

	# --------------------------------------------------------------------------------------------------------------------------------------------------------------- #
	def emailLog(self):
		"""This uses bash to email log """
		subject = self.appName + " script report"
		command = 'mail -s "'+subject+'" "'+self.email+'" < '+self.logFile+' '
		os.system(command)
		print "Email sent to: " + self.email
		self.log("Email sent to: " + self.email)

	# --------------------------------------------------------------------------------------------------------------------------------------------------------------- #
	def dbGetEntityId(self, sku):
		"""This gets entity_id with provided sku """
		cursor = self.dbConnect()
		query = "SELECT entity_id FROM catalog_product_entity WHERE sku = '"+str(sku)+ "'"
		cursor.execute(query, plain_query=False)
		for value in cursor:
			return value[0]

	# --------------------------------------------------------------------------------------------------------------------------------------------------------------- #
	def csvWrite(self, row, writefile):
		"""This writes to csv file """
		errorWriter = csv.writer(open(writefile, 'a'), quoting=csv.QUOTE_ALL)				
		errorWriter.writerow(row)

	# --------------------------------------------------------------------------------------------------------------------------------------------------------------- #
	def processFile(self):
		self.log('Processing csv file...')
		#Get config Values
		csvOne = str(self.compareCSVOne)
		csvTwo = str(self.compareCSVTwo)


		readerOne = csv.reader(open(self.compareCSVOne, "rb"))
		#readerTwo = csv.reader(open(self.compareCSVTwo, "rb"))

		for setOne in readerOne:
			print setOne



if __name__ == '__main__':

	#If arguments aren't passed show error message
	if len(sys.argv)<2:
		sys.exit('mageSkuToEntityId -- ERROR: Please provide configuration file!!')
	else:
		
		start_script = datetime.datetime.now()
		#Get the config file from the first argument passed to the script.
		config_file = str(sys.argv[1])
		#Load the config file into the class object and initiate. 
		mste = mageTableDiff(config_file)
		mste.scriptInfo()

		#Let's process all values from the config file.
		run_script = mste.processFile()
		

		end_script = datetime.datetime.now()
		script_time_taken = end_script - start_script
		print "Script time: " + str(script_time_taken)

		mste.log("Script time: " + str(script_time_taken))
		mste.log('Processing csv file completed')
		mste.emailLog()




