import json
try:
	with open('project_parameters.json') as f:
		jsondata = json.load(f)

except FileNotFoundError as e:
	print(e)

#from store_and_convert.py
mongoclient = jsondata["store_and_convert"]["mongoclient"]
basic_db = jsondata["store_and_convert"]["basic_db"]
back_up_db = jsondata["store_and_convert"]["back_up_db"]
txt_uuid = jsondata["store_and_convert"]["txt_uuid"]
path_txt_saves = jsondata["store_and_convert"]["path_txt_saves"]
path_to_project = jsondata["store_and_convert"]["path_to_project"]
allowed_files = jsondata["myflask"]["allowed_files"]



#from transfer 
path_to_outputs = jsondata["transfer"]["path_to_outputs"]


#from myflask.py
host_address = jsondata["myflask"]["host_address"]

class Config(object):
	DEBUG = jsondata["myflask"]["debug"]
	TESTING = jsondata["myflask"]["testing"]
	TEMPLATES_AUTO_RELOAD = jsondata["myflask"]["templates"]
	SECRET_KEY = jsondata["myflask"]["secret_key"]

	UPLOADS = jsondata["myflask"]["uploads"]
	ALLOWED_FILES = jsondata["myflask"]["allowed_files"]

class ProductionConfig(Config):
	pass

class DevelopmentConfig(Config):
	DEBUG = True

class TestingConfig(Config):
	TESTING = True
