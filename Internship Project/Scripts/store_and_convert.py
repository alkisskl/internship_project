#!/usr/bin/env python
# coding=utf-8
from __future__ import print_function
import os
import os.path
import time
from datetime import datetime , date , timedelta
import pymongo
from pymongo import MongoClient
import ast
import sys
from supplement import *
import shutil
import random

global data
data = {
	"string_time":'',
	"col_time": [],
	'lod_time': [],
	"dic_time" : {},
	"string_total_free_memory":'',
	"string_p_errors":'',
	"string_time":'',
	"string_vmem_usage":'',
	"string_mem_usage":'',
	"string_cpu_usage":'',
	"file" : [],
	"stats": [],
	"vmem_usage":[],
	"total_free_memory":[],
	"p_errors":[],
	"time" : [],
	"cpu_usage" : [],
	"mem_usage" : [],
	"dic_stats": {},
	"dic_errors" : {},
	"dic_total_free_memory": {},
	"dic_mem_usage": {},
	"dic_cpu_usage" : {},
	"dic_vmem_usage" : {},
	"lod_total_free_memory" : [],
	"lod_mem_usage" : [],
	"lod_cpu_usage" : [],
	"lod_vmem_usage" : [],
	"lod_errors": [],
	"lod_stats":[],
	"col_stats": [],
	"col_total_free_memory": [],
	"col_mem_usage": [],
	"col_cpu_usage": [],
	"col_vmem_usage": [],
	"col_errors" : [],
	"available_dates": [],
	"col_available_dates":[],
	"dic_available_dates": {},
	"lod_available_dates": [],
	"col_users": []
	}


#######
# ###################################################### STORE THE OUTPUT FROM THE STRESS TEST ####################################################
#######

def parse_list_strings():
	firstline = ''
	secondline = ''
	for line in data["file"]:
		curr = ''
		line = line.rstrip()
		if 'Times' in line:
			for i in line:
				if i =='[':
					start=line.index(i)
					curr = line[start:]
					realtime = ast.literal_eval(curr)
					avail_dates = realtime[0]
					avail_dates = avail_dates[0:10] + ' ' + avail_dates[-4:]
					data["available_dates"] = avail_dates # store only the dates
					pattern = "%a %b %d %H:%M:%S %Y"
					for i in realtime:
						curr2 = int(time.mktime(time.strptime(i, pattern))) # convert to epoch
						data["time"].append(curr2)

		elif '-duration_s' in line:
			firstline=line

		elif 'transactions' in line:
			if 'Historical' in line:
				line = line.replace("	"," ")
				secondline = line
			else:
				pass
		else:
			key = None
			if 'table_total_free_mem' in line:
				key = 'total_free_memory'
				string = 'string_total_free_memory'
			elif 'table_cpu_usage' in line:
				key = 'cpu_usage'
				string = 'string_cpu_usage'
			elif 'table_mem_usage' in line:
				key = 'mem_usage'
				string = 'string_mem_usage'
			elif 'table_vmem_usage' in line:
				key = 'vmem_usage'
				string = 'string_vmem_usage'
			elif 'ERRORS' in line:
				key = 'p_errors'
				string = 'string_p_errors'

			for i in line:
				if i =='[':
					start =line.index(i)
					curr = line[start:]
					if key:
						data[key] = ast.literal_eval(curr)
						for z in data[key]:
							data[string] = data[string] + str(z) + '_'


	for z in data["time"]:
		data["string_time"] = data["string_time"] + str(z) + '_'

	#header parse
	data["stats"] = '{} {}'.format(firstline, secondline)





#######
# ################################################# CHECK IF THE FILE HAS DATA ####################################################
#######

def check_and_backup_file():
	# if tables are empty just remove the txt file
	if not data["total_free_memory"] and not data["cpu_usage"] and not data["mem_usage"] and not data["vmem_usage"] and not data["p_errors"]:
		print('Empty Tables')
		os.remove(txt_uuid)
		return False

	# if txt is valid save it in folder: txt_saves and then store the tables in the db
	else:
		print("Valid File")
		date = data["available_dates"].replace(' ','_')
		os.makedirs(path_txt_saves, exist_ok=True)
		shutil.copy(txt_uuid, path_txt_saves)
		newfilename = path_txt_saves+ date +'_num_0'+ '.txt'
		path_txt_uuid = path_txt_saves + txt_uuid
		listdir_in_txt_saves = list(os.listdir(path_txt_saves))
		listdir_with_this_date = [y for y in listdir_in_txt_saves if date in y]

		#check if the newfilename already exists
		if os.path.isfile(newfilename):
			newfilename = path_txt_saves+ date + '_num_'+ str(len(listdir_with_this_date)) + '.txt'
			if os.path.isfile(newfilename) == False:
				os.rename(path_txt_uuid, newfilename)
		else:
			os.rename(path_txt_uuid, newfilename)

		return True


#######
# ##################################################### DATABASE WITH MONGO DB ###########################################################
#######

def connect_to_database():
	try:
		client = pymongo.MongoClient(mongoclient)
		mydb = client.mydatabase
		data["col_total_free_memory"] = mydb["total_free_memory"]
		data["col_mem_usage"] = mydb["mem_usage"]
		data["col_cpu_usage"] = mydb["cpu_usage"]
		data["col_vmem_usage"] = mydb["vmem_usage"]
		data["col_errors"] = mydb["p_errors"]
		data["col_stats"]= mydb["p_stats"]
		data["col_available_dates"] = mydb["available_dates"]
		data["col_time"] = mydb["time"]
		data["col_users"] = mydb["users"]


	except TimeoutError as e:
		print('TimeoutError from Db')
		raise e

######
# ################################################## CREATE THE COUNTER LISTS FROM DB #####################################
######

def get_run_counter():
	counters = {
		"counterlist" : [],
		"counterlistnums" : []
	}

	############################ Insert values in counterlist #######################################
	for i in range(0,data["col_cpu_usage"].find().count()):
		cursor = list(data["col_cpu_usage"].find({'run' : i}, {'_id': False}))
		if {'run' : i } in cursor:
			counters["counterlist"].extend(cursor)

	counters["counterlistnums"] = [list(x.values())[0] for i,x in enumerate(counters["counterlist"]) if i >= 0 ] #['1','2',...]

	return counters


#######
# ################################################### INCREMENT THE COUNTER IN DB #############################################################
#######

def increment_run_counter():
	counters = get_run_counter()
	counterlist = []
	############################ Insert values in counterlist #######################################
	run_index =0
	for i in range(0,data["col_cpu_usage"].find().count()):
		cursor = list(data["col_cpu_usage"].find({'run' : i}, {'_id': False}))
		if {'run' : i } in cursor:
			counterlist.extend(cursor)
			run_index =i
	new_run_index = run_index +1

	return new_run_index


#######
# #################################################### INSERT NEW VALUES IN DATABASE ########################################################
#######

def insert_in_my_db():
	counters = get_run_counter()
	new_run_index = increment_run_counter()
	string_for_db = 'run' + str(new_run_index)
	# ####################################################### Dictionaries ###############################################################
	data["dic_total_free_memory"][string_for_db]=str(data["string_total_free_memory"])
	data["dic_mem_usage"][string_for_db]=str(data["string_mem_usage"])
	data["dic_cpu_usage"][string_for_db]=str(data["string_cpu_usage"])
	data["dic_vmem_usage"][string_for_db]=str(data["string_vmem_usage"])
	data["dic_errors"][string_for_db]=str(data["string_p_errors"])
	data["dic_time"][string_for_db]=str(data["string_time"])

	data["dic_stats"][string_for_db]=str(data["stats"])
	data["dic_available_dates"][string_for_db]=str(data["available_dates"])
	data["time"] = []

	############################################################# List of dictionaries ####################################################
	stats_map = [
		{ 'k_in': 'dic_total_free_memory' , 'k_out': 'lod_total_free_memory'},
		{ 'k_in': 'dic_cpu_usage' , 'k_out': 'lod_cpu_usage'},
		{ 'k_in': 'dic_mem_usage' , 'k_out': 'lod_mem_usage'},
		{ 'k_in': 'dic_vmem_usage' , 'k_out': 'lod_vmem_usage'},
		{ 'k_in': 'dic_errors' , 'k_out': 'lod_errors'},
		{ 'k_in': 'dic_stats' , 'k_out': 'lod_stats'},
		{ 'k_in': 'dic_available_dates' , 'k_out': 'lod_available_dates'},
		{ 'k_in': 'dic_time' , 'k_out': 'lod_time'},
	]

	for stat in stats_map:
		data[stat["k_out"]] = []
		for k,v in data[stat['k_in']].items():
			data[stat['k_out']].append({str(k):str(v)})

	# ####################################################### Insert in Collections ################################################
	col1 = data["col_total_free_memory"].insert_many(data["lod_total_free_memory"])
	col2 = data["col_mem_usage"].insert_many(data["lod_mem_usage"])
	col3 = data["col_cpu_usage"].insert_many(data["lod_cpu_usage"])
	col4 = data["col_vmem_usage"].insert_many(data["lod_vmem_usage"])
	col5 = data["col_errors"].insert_many(data["lod_errors"])
	col6 = data["col_stats"].insert_many(data["lod_stats"])
	col7 = data["col_available_dates"].insert_many(data["lod_available_dates"])
	col8 = data["col_time"].insert_many(data["lod_time"])

	# ############################################ Add the counter #################################################
	data["col_total_free_memory"].insert_one({'run': new_run_index })
	data["col_mem_usage"].insert_one({'run': new_run_index })
	data["col_cpu_usage"].insert_one({'run': new_run_index })
	data["col_vmem_usage"].insert_one({'run': new_run_index })
	data["col_errors"].insert_one({'run': new_run_index })
	data["col_stats"].insert_one({'run': new_run_index })
	data["col_available_dates"].insert_one({'run': new_run_index })
	data["col_time"].insert_one({'run': new_run_index })
	os.remove(txt_uuid)

	# ######################################## Clear out the lists and the dics #####################################
	for stat in stats_map:
		data[stat["k_out"]] = []
		data[stat["k_in"]] = {}



######
# ############################################# TRANSFORM THE DATABASE LISTS TO LIST WITH FLOATS AND INTS #########################################################
######

def transform_database_lists(input_list_from_key_values_function):

	curr_lista=[]
	output_list = []
	curr_string = ''
	for i in input_list_from_key_values_function:
		if isinstance(i, int):
			output_list.append(int(i))
		else:
			x = str(i).rstrip()
			for z in x:
				try:
					float(z)
					curr_lista.append(z)
				except:
					for y in curr_lista:
						curr_string = curr_string + y
					output_list.append(float(curr_string))
					curr_string = ''
					curr_lista = []

	return output_list

######
# ################################################ CREATE LISTS OF VALUES AND KEYS ##################################################################
#####

def keys_values_lists():
	pattern = "%a %b %d %H:%M:%S %Y"
	counters = get_run_counter()
	keys_values = {
		"all_k_v_total_free_memory":[],
		"k_v_total_free_memory":[],
		"v_total_free_memory":[],
		"total_free_memory_val_with_counter" :[],
		"k_total_free_memory" :[],
		"all_k_v_mem_usage" : [],
		"k_v_mem_usage" : [],
		"v_mem_usage" : [],
		"mem_usage_val_with_counter" : [],
		"k_mem_usage" : [],
		"all_k_v_cpu_usage" : [],
		"k_v_cpu_usage" : [],
		"v_cpu_usage" : [],
		"cpu_usage_val_with_counter" : [],
		"k_cpu_usage" : [],
		"all_k_v_vmem_usage" : [],
		"k_v_vmem_usage" : [],
		"v_vmem_usage" : [],
		"vmem_usage_val_with_counter" : [],
		"k_vmem_usage" : [],
		"all_k_v_errors" : [],
		"k_v_errors" : [],
		"v_errors" : [],
		"errors_val_with_counter" : [],
		"k_errors" : [],
		"all_k_v_stats" : [],
		"k_v_stats" : [],
		"v_stats" : [],
		"k_epoch_total_free_memory" : [],
		"k_epoch_mem_usage" : [],
		"k_epoch_cpu_usage" : [],
		"k_epoch_vmem_usage" : [],
		"k_epoch_errors" : [],
		"all_k_v_available_dates":[],
		"k_v_available_dates":[],
		"v_available_dates":[],
		'all_k_v_time': [],
		'col_time': [],
		'k_v_time': [],
		'k_time': [],
		'v_time': [],
		'time_val_with_counter': [],
		'k_epoch_time': [],
		'non_epoch_time':[]
	}

	# Total Free Memory, Used Memory, Cpu Usage, Vmem Usage, Errors

	stats_map = [
		{
			'all': 'all_k_v_total_free_memory',
			'col': 'col_total_free_memory',
			'k_v': 'k_v_total_free_memory',
			'k': 'k_total_free_memory',
			'v': 'v_total_free_memory',
			'total_counter': 'total_free_memory_val_with_counter',
		},

		{
			'all': 'all_k_v_mem_usage',
			'col': 'col_mem_usage',
			'k_v': 'k_v_mem_usage',
			'k': 'k_mem_usage',
			'v': 'v_mem_usage',
			'total_counter': 'mem_usage_val_with_counter',
		},

		{
			'all': 'all_k_v_vmem_usage',
			'col': 'col_vmem_usage',
			'k_v': 'k_v_vmem_usage',
			'k': 'k_vmem_usage',
			'v': 'v_vmem_usage',
			'total_counter': 'vmem_usage_val_with_counter',
		},

		{
			'all': 'all_k_v_cpu_usage',
			'col': 'col_cpu_usage',
			'k_v': 'k_v_cpu_usage',
			'k': 'k_cpu_usage',
			'v': 'v_cpu_usage',
			'total_counter': 'cpu_usage_val_with_counter',
		},

		{
			'all': 'all_k_v_errors',
			'col': 'col_errors',
			'k_v': 'k_v_errors',
			'k': 'k_errors',
			'v': 'v_errors',
			'total_counter': 'errors_val_with_counter',
		},

		{
			'all': 'all_k_v_time',
			'col': 'col_time',
			'k_v': 'k_v_time',
			'k': 'k_time',
			'v': 'v_time',
			'total_counter': 'time_val_with_counter',
		}

	]


	for stat in stats_map:
		keys_values[stat['all']] = list(data[stat['col']].find({}, {'_id': False})) # list with all keys and values 
		keys_values[stat['k_v']] = [n for n in keys_values[stat['all']] if n not in counters["counterlist"]] # list with all keys and values  without the running counter
		keys_values[stat['v']] = [list(x.values())[0] for i, x in enumerate(keys_values[stat['k_v']]) if i >= 0 ] # list with only the values
		keys_values[stat['total_counter']]=[list(x.values())[0] for i, x in enumerate(keys_values[stat['all']]) if i >= 0 ] # list with the values and the counter
		#transform_database_lists
		keys_values[stat['total_counter']] = transform_database_lists(keys_values[stat['total_counter']])
		keys_values[stat['v']] = transform_database_lists(keys_values[stat['v']])

	# Stats
	keys_values["all_k_v_stats"] = list(data["col_stats"].find({}, {'_id': False}))
	keys_values["k_v_stats"] = [n for n in keys_values["all_k_v_stats"] if n not in counters["counterlist"] ]
	keys_values["v_stats"] = [list(x.values())[0] for i,x in enumerate(keys_values["k_v_stats"]) if i >= 0 ]

	#Availabe Dates
	keys_values["all_k_v_available_dates"] = list(data["col_available_dates"].find({}, {'_id': False}))
	keys_values["k_v_available_dates"] = [n for n in keys_values["all_k_v_available_dates"] if n not in counters["counterlist"] ]
	keys_values["v_available_dates"] = [list(x.values())[0] for i,x in enumerate(keys_values["k_v_available_dates"]) if i >= 0 ]

	for i in keys_values['v_time']:
		i=int(i)
		curr = ''
		curr = time.strftime(pattern, time.localtime(i))
		keys_values['non_epoch_time'].append(curr)

	return keys_values




######
# ####################################################### CALCULATOR WHEN SPECIFIC DATE RANGE GIVEN ########################################################
######

def specific_date(input1,input2,where):
	keys_values = keys_values_lists()
	range_check = [i for i in range(0, 10)]
	############################# Where initialization ###################################
	if where == 'total_free_memory':
		sp_date_values = keys_values["v_total_free_memory"]
	elif where == 'mem_usage':
		sp_date_values = keys_values["v_mem_usage"]
	elif where == 'cpu_usage':
		sp_date_values = keys_values["v_cpu_usage"]
	elif where == 'vmem_usage':
		sp_date_values = keys_values["v_vmem_usage"]
	elif where == 'errors':
		sp_date_values = keys_values["v_errors"]
	sp_date_keys = keys_values['non_epoch_time']



	try:
	################################# Input transfrom ###################################

		month1 = input1[0:3]
		day1 = ''
		year1 = input1[-4] + input1[-3] + input1[-2] + input1[-1]
		indexday1=[]
		for i in input1:
			if str(i) in '0,1,2,3,4,5,6,7,8,9':
				indexday1.append(i)
		if len(indexday1) == 5:
			day1 = indexday1[0]
		else:
			day1 = indexday1[0] + indexday1[1]


		month2 = input1[0:3]
		day2 = ''
		year2 = input1[-4] + input1[-3] + input1[-2] + input1[-1]
		indexday2=[]
		for i in input2:
			if  str(i) in '0,1,2,3,4,5,6,7,8,9' :
				indexday2.append(i)
		if len(indexday2) == 5:
			day2 = indexday2[0]
		else:
			day2 = indexday2[0] + indexday2[1]

		############################# Searching for the inputs in Db ###########################
		format_date1 = '{} {}'.format(month1 , day1)
		format_date2 = '{} {}'.format(month2 , day2)

		first_index_finder=[]
		last_index_finder=[]


		for i in sp_date_keys:

			if format_date1 in i and i != 'run':
				if year1 in i:
					first_index_finder.append(sp_date_keys.index(i))
				else:
					pass

			if format_date2 in i and i != 'run':
				if year2 in i:
					last_index_finder.append(sp_date_keys.index(i))
				else:
					pass

		first_index = int(first_index_finder[0])#first requested value
		last_index = int(last_index_finder[-1])#last requested value

		############################## Store the results ###################################

		return (sp_date_keys[first_index:last_index],sp_date_values[first_index:last_index])

	except IndexError:
		print('IndexError')


######
# ######################################################## CALCULATOR WHEN SPECIFIC RUNS RANGE GIVEN ###################################################
######

def specific_runs(x,y,what,where):
	keys_values = keys_values_lists()
	firstrun = x
	lastrun = y
	current_list = []
	run_range = [i for i in range(int(firstrun),int(lastrun)+1)]#list with all the numbers included in the run range(for plot)
	output_for_run_range = []
	avg_output_for_run_range=[]

	############################# Where initialization ###################################
	if where == 'total_free_memory':
		sp_run_keys = keys_values["total_free_memory_val_with_counter"]
	elif where == 'mem_usage':
		sp_run_keys = keys_values["mem_usage_val_with_counter"]
	elif where == 'cpu_usage':
		sp_run_keys = keys_values["cpu_usage_val_with_counter"]
	elif where == 'vmem_usage':
		sp_run_keys = keys_values["vmem_usage_val_with_counter"]
	elif where == 'errors':
		sp_run_keys = keys_values["errors_val_with_counter"]


	############################################ Average per specific runs ######################################
	if what == 'avg':
		avg_cpu_usage = 0

		for i in sp_run_keys:
			if isinstance(i, int):
				if firstrun -1 == int(i):
					current_list.clear()
					i+=1

				elif firstrun == int(i):
					firstrun += 1
					for x in current_list:
						avg_cpu_usage = avg_cpu_usage + float(x)
					avg_cpu_usage = avg_cpu_usage/len(current_list)
					avg_output_for_run_range.append(avg_cpu_usage) #store in this list the average value of every run
					if lastrun == int(i):
						break
					else:
						current_list.clear()
						avg_cpu_usage = 0

			elif isinstance(i, float):
				current_list.append(i)
		return (run_range , avg_output_for_run_range)


	# ################################################# All for specific runs ###################################################
	elif what == 'all':
		temporary_values_list = []
		for i in sp_run_keys:
			if isinstance(i, int):
				if firstrun -1 == int(i):
					current_list.clear()
					i+=1

				elif firstrun == int(i):
					firstrun += 1
					for x in current_list:
						temporary_values_list.append(x)
					output_for_run_range.append(temporary_values_list) #store in this list all the values of every run

					if lastrun == int(i):
						break

					else:
						current_list.clear()
						temporary_values_list = []

			elif isinstance(i, float):
				current_list.append(i)

		output_for_run_range = [j for sub in output_for_run_range for j in sub]
		return output_for_run_range

	else:
		pass


#######
# ################################################################# AVERAGE CALCULATOR ###################################################################
#######

def averagevalues(where):
	avg_values = []
	keys_values = keys_values_lists()
	if where == 'total_free_memory':
		avg_keys = keys_values["total_free_memory_val_with_counter"]
	elif where == 'mem_usage':
		avg_keys = keys_values["mem_usage_val_with_counter"]
	elif where == 'cpu_usage':
		avg_keys = keys_values["cpu_usage_val_with_counter"]
	elif where == 'vmem_usage':
		avg_keys = keys_values["vmem_usage_val_with_counter"]
	elif where == 'errors':
		avg_keys = keys_values["errors_val_with_counter"]

	# ################################## Calculate average value per run and store them in a list #######################################
	current_run = 1
	current_list = []
	for i in avg_keys:

		if isinstance(i, int) :
			avg_total = 0.0
			current_run += 1
			for x in current_list:
				avg_total = avg_total + float(x)

			try:
				avg_total = avg_total/len(current_list)
			except ZeroDivisionError:
				avg_total = 0.0

			avg_values.append(avg_total)
			current_list.clear()

		elif isinstance(i, float):
			current_list.append(i)

	return avg_values


#######
# ################################################# CALCULATE THE AVG VALUE FOR A SPECIFIC DATE ##################################################
#######

def avg_per_date(date_input,where):
	keys_values = keys_values_lists()
	monthConversions = {
		"01":"Jan",
		"02":"Feb",
		"03":"Mar",
		"04":"Apr",
		"05":"May",
		"06":"Jun",
		"07":"Jul",
		"08":"Aug",
		"09":"Sep",
		"10":"Oct",
		"11":"Nov",
		"12":"Dec"
		}

	############################ Where initialization ###################################
	if where == 'total_free_memory':
		sp_date_values = keys_values["v_total_free_memory"]
	elif where == 'mem_usage':
		sp_date_values = keys_values["v_mem_usage"]
	elif where == 'cpu_usage':
		sp_date_values = keys_values["v_cpu_usage"]
	elif where == 'vmem_usage':
		sp_date_values = keys_values["v_vmem_usage"]
	elif where == 'errors':
		sp_date_values = keys_values["v_errors"]
	sp_date_keys = keys_values["non_epoch_time"]

	############################################## Date_Input Convert ##############################################
	year1 = date_input[0:4]
	month1 = date_input[5:7]#01
	month1 = monthConversions[str(month1)]#01 -->"Jan"
	day1 = date_input[8:]
	format_date1 = '{} {}'.format(month1 , day1)#Jan 1
	format_date2 = '{} {} {}'.format(month1 , day1, year1)#Jan 1 2019


	################################ If date exist calculate avg else avg = 0 #####################################
	for alldates in keys_values["v_available_dates"]:
		if format_date2 in alldates:
			avg_for_this_date = 0.0
			listagiaindex=[]
			for x in sp_date_keys:
				try:
					if format_date1 in x :
						if year1 in x:
							listagiaindex.append(sp_date_keys.index(x))
					else:
						pass
				except:
					print('Bad Input')

			firstint = int(listagiaindex[0])
			lastint = int(listagiaindex[-1])

			values  = sp_date_values[firstint:lastint]

			curr_sum = 0.0
			for i in values:
				curr_sum += float(i)
			avg_for_this_date = curr_sum/len(values)
			break

		else:
			avg_for_this_date = 0.0

	return(avg_for_this_date)


#######
# ######################################### CALCULATE ALL THE DAYS BETWEEN A GAP AND RETURN THE DAYS AND AVG FOR EACH DATE #############################
#######

def date_calculator(date_input1,date_input2,where):
	keys_values = keys_values_lists()
	monthConversions = {
		"Jan":"1",
		"Feb":"2",
		"Mar":"3",
		"Apr":"4",
		"May":"5",
		"Jun":"6",
		"Jul":"7",
		"Aug":"8",
		"Sep":"9",
		"Oct":"10",
		"Nov":"11",
		"Dec":"12"
		}

	############################################## Date_Input1 Convert ##############################################
	month1 = date_input1[0:3] #Jan
	month1 = monthConversions[str(month1)] #"Jan" --> 1
	day1 = ''
	year1 = date_input1[-4] + date_input1[-3] + date_input1[-2] + date_input1[-1]
	############ Day1 finder ################
	indexday1=[]
	for i in date_input1:
		if  str(i) in '0,1,2,3,4,5,6,7,8,9' :
			indexday1.append(i)
	if len(indexday1) == 5:
		day1 = indexday1[0]
	else:
		day1 = indexday1[0] + indexday1[1]

	############################################## Date_Input2 Convert ##############################################
	month2 = date_input2[0:3]
	month2 = monthConversions[str(month2)]
	day2 = ''
	year2 = date_input2[-4] + date_input2[-3] + date_input2[-2] + date_input2[-1]
	############ Day2 finder ################
	indexday2=[]
	for i in date_input2:
		if  str(i) in '0,1,2,3,4,5,6,7,8,9' :
			indexday2.append(i)
	if len(indexday2) == 5:
		day2 = indexday2[0]
	else:
		day2 = indexday2[0] + indexday2[1]
	date1 = date(int(year1),int(month1), int(day1))
	date2 = date(int(year2),int(month2), int(day2))



	######################################## Calculate all the days between the gap ########################################
	wanted_days = []
	delta = date2 - date1
	for i in range(delta.days + 1):
		x = date1 + timedelta(i)
		wanted_days.append(str(x))

	######################################## Calculate the avg_value for every date ########################################
	avg_values_for_wanted_days = []
	for one_day in wanted_days:
		avg_values_for_wanted_days.append(avg_per_date(one_day,where)) # avg_per_date() func call



	############################################# Ignore all the values = 0 ##############################################
	dic_wanted_days = {}
	for i in range(len(wanted_days)): #create dictionary (keys:dates, values: avg)
		dic_wanted_days[str(wanted_days[i])]=float(avg_values_for_wanted_days[i])

	dic_wanted_days = {k:v for k,v in dic_wanted_days.items() if v!=0} # values != 0

	wanted_days = []
	for i in dic_wanted_days.keys():
		wanted_days.append(i)

	avg_values_for_wanted_days = []
	for i in dic_wanted_days.values():
		avg_values_for_wanted_days.append(i)


	return wanted_days,avg_values_for_wanted_days

#######
# ################################################### CONVERT ALLOWED FILES LIST FROM FLASK TO .file_type #########################################################################
#######
def allowed_file_conversion():
	# "['TXT','DOC']"---->['.txt','.doc']
	allowed_string = allowed_files.replace('[','')
	allowed_string = allowed_string.replace(']','')
	allowed_string = allowed_string.replace("'",'')
	allowed_string.lower()
	allowed_file_types = []
	curr_allowed_file_types = []
	curr_allowed_file_types = allowed_string.split(',')
	for item in curr_allowed_file_types:
		item = '.' + item.lower()
		allowed_file_types.append(item)


	return allowed_file_types


#######
# ############################################################## MAIN ###############################################################################
#######

def mymain():
	try:
		source = os.listdir(path_to_project)
		allowed_file_types = allowed_file_conversion()

		#for every valid file type:
		for allowed_file_type in allowed_file_types:
			for files in source:
				#take all the txt files in the project folder
				if files.endswith(allowed_file_type):
					print(files)
					file = files
					##################### txt file not empty #####################
					if os.stat(file).st_size != 0:
						print('file found and its not empty')
						os.rename(file, txt_uuid)
						with open(txt_uuid, encoding = "ISO-8859-1") as fp:
							data["file"] = fp.read().split('\n')
							parse_list_strings()
							if check_and_backup_file():
								connect_to_database()
								increment_run_counter()
								insert_in_my_db()


								return True

							else:
								return False

					######################### txt file empty ##########################
					else:
						print('empty file')
						os.remove(file)
						return False


	##################### txt file doesnt exist ###########################
	except FileNotFoundError:
		print('file doesnt exist')


if __name__ == '__main__':

	mymain()
