#INTRODUCTION
This project i fulfilled at my Internship Programm at Citrix in Patras.

#MAIN TASK
Build an analytic tool for the results of the Stress Tests consisted of:
	- A Python script that consumes the data from the stress tests.
	- A Mongo DB database that persistently holds the result for the stress runs and users profiles.
	- A front-end server (Flask/python) that exposes the graphs to the end authenticated user.

#FILES
store_and_convert.py
	- edit,import data in the database
	- make lists from the database to make the plots
	- functions with input these lists, return lists for more specific plots (per run , per date)

myflask.py
	- make the flask server
	- help to communicate the back-end and the front-end
	- set the front-end routes
	- plot functions

project_parametes_template.json
	- json configuration file

supplement.py
	- set the values for the configuration file

transfer.py
	- transfer all the valid txt's from a specific folder to project folder 
	  so the store_and_convert.py script can use it for input in the database

template folder
	- all the html files
	- plot folder, here will be saved all the plots after they made

static folder
	- css files
	- image files for the site

txt_saves folder
	- here will be saved all the valis txt's

