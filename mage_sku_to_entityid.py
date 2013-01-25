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




class mageSkuToEntityId(object):
	"""Convert Sku's into Entity_ids """
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
				if(configValues[0] == 'HOST'):
					self.dbHost1 = configValues[1]
					self.dbHost2 = configValues[1]   
				if(configValues[0] == 'DATABASE'):
					self.database = configValues[1]
				if(configValues[0] == 'PASSWORD'):
					self.dbPassword = configValues[1]
				if(configValues[0] == 'USERNAME'):
					self.dbUsername = configValues[1]
				if(configValues[0] == 'CSVREAD'):
					self.csvFile = configValues[1]
				if(configValues[0] == 'CSVWRITE'):
					self.csvFileWrite = configValues[1]
				if(configValues[0] == 'CSVSKUCOLUMN'):
					self.entitySkuColumn = configValues[1]
				if(configValues[0] == 'CSVATTRIBUTECOLUMN'):
					self.attributeIdColumn = configValues[1]
				if(configValues[0] == 'EMAIL'):
					self.email = configValues[1]
				if(configValues[0] == 'LOG'):
					self.logFile = configValues[1]
					#Let's remove old log and csv files at the end here. 
					self.removeOldFile(self.logFile)
					self.removeOldFile(self.csvFileWrite)

		else:
			sys.exit('mageSkuToEntityId -- ERROR: Please provide configuration file!!')

	    
	# --------------------------------------------------------------------------------------------------------------------------------------------------------------- #
	def scriptInfo(self):
		"""This just displays script information """
		memory_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
		self.log("The script " + str(self.appName) + " was ran at " + str(datetime.datetime.now()))
		self.log("Script ran on host: " + str(self.dbHost1))
		self.log("Using csv file: " + str(self.csvFile))
		self.log("Using write csv file: " + str(self.csvFileWrite))
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
		sku_column = int(self.entitySkuColumn)
		attribute_id_column = int(self.attributeIdColumn)
		
		#Let's read the csv file
		reader = csv.reader(open(self.csvFile, "rb"))
		count = 1
		for row in reader:
			sku = row[sku_column]
			attribute_value = row[attribute_id_column]

			entity_id = self.dbGetEntityId(sku)

			if(entity_id != None):
				time.sleep(0.01) #This fixes a oursql persistent connection bug??
				print 'SKU: ' + str(sku) + ' ENTITY_ID: ' + str(entity_id) + ' ATTRIBUTE_VALUE: ' + str(attribute_value)
				self.csvWrite([sku, entity_id, attribute_value], self.csvFileWrite)
							
			count = count + 1


if __name__ == '__main__':

	#If arguments aren't passed show error message
	if len(sys.argv)<2:
		sys.exit('mageSkuToEntityId -- ERROR: Please provide configuration file!!')
	else:
		
		start_script = datetime.datetime.now()
		#Get the config file from the first argument passed to the script.
		config_file = str(sys.argv[1])
		#Load the config file into the class object and initiate. 
		mste = mageSkuToEntityId(config_file)
		mste.scriptInfo()

		mste.csvWrite(['sku', 'entity_id', 'attribute_value'], mste.csvFileWrite)

		#Let's process all values from the config file.
		run_script = mste.processFile()
		end_script = datetime.datetime.now()
		script_time_taken = end_script - start_script
		print "Script time: " + str(script_time_taken)

		mste.log("Script time: " + str(script_time_taken))
		mste.log('Processing csv file completed')
		mste.emailLog()




