#!/usr/bin/env python

################################################################################
## NAME: MAGENTO ATTRIBUTE IMPORTER - Version 0.0.1
## DATE: Feb 2012
## AUTHOR: Jason R Alexander
## MAIL: JasonAlexander@zumiez.com
## SITE: http://www.zumiez.com
## INFO: This script will import magento product attributes using a confi file and a source csv file. 
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


class mageAttributeImporter(object):
	""" This import Magento attribute values from a csv file"""
	# --------------------------------------------------------------------------------------------------------------------------------------------------------------- #
	def __init__(self, config_file):
		#Get the name of the script
		self.appName = str(os.path.splitext(os.path.basename(__file__))[0])
		#Let's spot check out replace progress
		self.spotCheckList = [100, 500, 800, 1000, 2500, 5000, 7500, 10000, 12500, 15000, 20000, 20500, 21000]
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
				if(configValues[0] == 'CSV'):
					self.csvFile = configValues[1]
				if(configValues[0] == 'DRYRUN'):
					self.dryRun = configValues[1]
				if(configValues[0] == 'ATTRIBUTEID'):
					self.attributeId = configValues[1]
				if(configValues[0] == 'CSVENTITYCOLUMN'):
					self.entityIdColumn = configValues[1]
				if(configValues[0] == 'CSVATTRIBUTECOLUMN'):
					self.attributeIdColumn = configValues[1]
				if(configValues[0] == 'EMAIL'):
					self.email = configValues[1]
				if(configValues[0] == 'LOG'):
					self.logFile = configValues[1]
					#Let's delete the old file
					self.removeOldFile(self.logFile)
				#if(configValues[0][0] == '#'):
					#self.log(configValues[0])


		else:
			sys.exit('mageAttributeImporter -- ERROR: Please provide configuration file!!')

	# --------------------------------------------------------------------------------------------------------------------------------------------------------------- #
	def scriptInfo(self):
		"""This just displays script information """
		memory_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
		self.log("The script " + str(self.appName) + " was ran at " + str(datetime.datetime.now()))
		self.log("Script ran on host: " + str(self.dbHost1))
		self.log("Updating attribute_id: " + str(self.attributeId))
		self.log("Using csv file: " + str(self.csvFile))
		self.log("Using log file: " + str(self.logFile))
		self.log("Dry-run status: " + str(self.dryRun))
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
	def dbCheckAttributeValue(self, entity_id, attribute_id):
		"""This check the attribute value """
		cursor = self.dbConnect()
		query = 'SELECT value FROM catalog_product_entity_varchar WHERE entity_id = '+entity_id+' AND attribute_id = '+attribute_id+' AND entity_type_id = 4'
		try:
			cursor.execute(query, plain_query=False)
			data = cursor.fetchall()

			for value in data:
				return value[0]
		except:
			return False

	# --------------------------------------------------------------------------------------------------------------------------------------------------------------- #
	def dbReplaceAttribute(self, entity_id, attribute_id, attribute_value):
		"""Replace the value in the db """
		cursor = self.dbConnect()
		query = 'REPLACE INTO catalog_product_entity_varchar (entity_type_id, attribute_id, store_id, entity_id, value) VALUES (4, '+attribute_id+', 0, '+entity_id+', "'+attribute_value+'")'

		if(self.dryRun == 'true'):
			return "[DRY-RUN] Query running: " + query
		else:
			cursor.execute(query, plain_query=False)
			cursor.close()
			return "Query running: " + query


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
	def processFile(self):
		self.log('Processing csv file...')
		#Get config Values
		entity_id_column = int(self.entityIdColumn)
		attribute_id_column = int(self.attributeIdColumn)
		attribute_id = str(self.attributeId)
		#Let's read the csv file
		reader = csv.reader(open(self.csvFile, "rb"))
		count = 1
		for row in reader:
			#Let's get the column values for the csv file
			entity_id = row[entity_id_column]
			attribute_value = row[attribute_id_column]
			#Going to check to see if the product has a attribute, kind of an unneccessary action?, But it weeds out csv crap
			check_attribute = self.dbCheckAttributeValue(entity_id, attribute_id)
			if(check_attribute):
				#Let's replace it!
				replace = self.dbReplaceAttribute(entity_id, attribute_id, attribute_value)
				time.sleep(0.01) #This fixes a oursql persistent connection bug??
				print str(count) + ") " + replace
				count = count + 1
				if count in self.spotCheckList:
					self.log("spot check on entity_id: " + str(entity_id) + " count is: " + str(count) + " OK!")	

			else:
				self.log('No attribute value for ' + str(entity_id) + ' value: ' + str(check_attribute))



if __name__ == '__main__':

	#If arguments aren't passed show error message
	if len(sys.argv)<2:
		#print generateHeader()
		sys.exit('mageAttributeImporter -- ERROR: Please provide configuration file!!')
	else:
		
		start_script = datetime.datetime.now()
		#Get the config file from the first argument passed to the script.
		config_file = str(sys.argv[1])
		#Load the config file into the class object and initiate. 
		mai = mageAttributeImporter(config_file)
		mai.scriptInfo()

		#Let's process all values from the config file.
		run_script = mai.processFile()
		end_script = datetime.datetime.now()
		script_time_taken = end_script - start_script
		print "Script time: " + str(script_time_taken)

		mai.log("Script time: " + str(script_time_taken))
		mai.log('Processing csv file completed')
		mai.emailLog()







