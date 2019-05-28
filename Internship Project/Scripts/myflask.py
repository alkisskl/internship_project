#!/usr/bin/env python
# coding=utf-8
from store_and_convert import *
from flask import Flask, render_template, url_for,send_file ,jsonify, request, redirect, Response , session
from werkzeug.utils import secure_filename
from flask_pymongo import PyMongo
import bcrypt
import random, json
import sys
import plotly 
import plotly.plotly as py
import plotly.graph_objs as go
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
from plotly import tools


app = Flask(__name__)
app.config.from_object("supplement.ProductionConfig")

######
# ############################## CONVERT THE FORMAT OF THE RETURN DATE FROM HTML TO THE FORMAT IS STORED IN DB #######################################
######
monthConversions = {
    "01": "January",
    "02": "February",
    "03": "March",
    "04": "April",
    "05": "May",
    "06": "June",
    "07": "July",
    "08": "August",
    "09": "September",
    "10": "October",
    "11": "November",
    "12": "December"
}

def dateconversions(date):
    year = date[0:4]
    month = date[5:7]
    month = monthConversions[str(month)]
    if len(date) == 9:
        day = date[-1]
    else:
        day = date[-2] + date[-1]
    full_date = '{} {} {}'.format(month,day,year)

    return full_date

######
# ######################################## CHECK IF THE UPLOADED FILES ARE IN RIGHT TYPE ##################################
######


def request_object_is_txt(filename):

    if not "." in filename:
        return False

    ext = filename.rsplit(".",1)[1]
    if ext.upper() in app.config["ALLOWED_FILES"]:
        return True
    else:
        return False



######
# ########################################################### ROUTES ###############################################################################
######


######
# Home
######
@app.route('/')
def home():
    #after login
    if 'username' in session:
        return redirect(url_for('yourhome'))

    #without log in
    return render_template('home.html')


######
# Home after login
######
@app.route('/yourhome', methods=['GET','POST'])
def yourhome():
    your_username = session['username']
    return render_template('after_success_login.html',your_username = your_username)


######
# Logout
######
@app.route('/logout', methods=['GET','POST'])
def logout():
    session.clear()
    return redirect(url_for('home'))


######
# Login
######
@app.route('/login', methods=['GET','POST'])
def login():
    connect_to_database()
    fail_message = 'Invalid Username or Password!'
    try:
        login_user = data["col_users"].find_one({'name': request.form['username']}) 

        if login_user == None:
            login_user = data["col_users"].find_one({'email': request.form['username']})

        login_pass = login_user['password']
        login_name = login_user['name']
    except TypeError:
        return render_template('home.html',fail_message = fail_message)


    if login_user:
        if bcrypt.hashpw(request.form['password'].encode('utf-8'), login_user['password']) == login_user['password']:
            session['username'] = login_name
            return redirect(url_for('home'))
    return render_template('home.html',fail_message = fail_message)


######
# Register
######
@app.route('/register', methods=['GET', 'POST'])
def register():
    if  request.method == 'POST':
        connect_to_database()
        existing_user = data["col_users"].find_one({'name': request.form['username']})
        existing_email = data["col_users"].find_one({'email': request.form['user_email']})

        if existing_user is None and existing_email is None:
            #hashing password and add salt
            hashpash = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
            #insert in database
            data["col_users"].insert({'name' : request.form['username'] ,'email': request.form['user_email'] ,'password' : hashpash })
            session['username'] = request.form['username']
            return redirect(url_for('home'))
        fail_message = 'This username or email already exists!'
        return render_template('register.html',fail_message = fail_message)
    return render_template('register.html')


######
# Upload
######
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'username' in session:
        return_of_my_main = False

        if request.method == "POST":
            try:
                if request.files:
                    new_file = request.files["file"]

                    if new_file.filename == "":
                        print("No filename")
                        return redirect('/fail_upload')

                    if not request_object_is_txt(new_file.filename):
                        print("Not allowed file type")
                        return redirect('/fail_upload')

                    else:
                        print("YOU UPLOAD A TXT")
                        filename = secure_filename(new_file.filename)
                        filename ="stress_result.txt"
                        new_file.save(os.path.join(app.config["UPLOADS"], filename))
                        return_of_my_main = mymain()
                        if return_of_my_main:
                            return redirect('/success_upload')
                        else:
                            return redirect('/fail_upload')
                        print(return_of_my_main)

                    return redirect(request.url)
            except Exception as e:
                print(e)
                return redirect('/fail_upload')

        return render_template('upload.html')

    return render_template('home.html')


######
# If uploaded the file successfully
#####
@app.route('/success_upload')
def success_upload():
    return render_template('success_upload.html')


######
# If uploaded a wrong file
#####
@app.route('/fail_upload')
def fail_upload():
    return render_template('fail_upload.html')


######
# Make Your Own Plots
######
@app.route('/function', methods = ['GET','POST'])
def function():
    if 'username' in session:
        return render_template('function.html')
    return render_template('home.html')

@app.route('/receiver', methods = ['GET','POST'])
def worker():
    global val_dic
    val_dic={
        "radio": "",
        "firstdate": "",
        "secondate" : "",
        "firstrun" : "",
        "secondrun" : "",
        "radio_obj" : "",
        "radio_all_avg" : ""
    }
    if request.method != 'POST':
        return

    ###################################### Input from post #######################################
    else:
        if 'radio' in request.form:
            val_dic["radio"] = request.form['radio']
        if 'firstdate' in request.form:
            val_dic["firstdate"] = request.form['firstdate']
        if 'secondate' in request.form:
            val_dic["secondate"] = request.form['secondate']
        if 'radio_obj' in request.form:
            val_dic["radio_obj"] = request.form['radio_obj']
        if 'radio_all_avg' in request.form:
            val_dic["radio_all_avg"] = request.form['radio_all_avg']
        try:
            val_dic["firstrun"] = int(request.form['firstrun'])
            val_dic["secondrun"] = int(request.form['secondrun'])
        except:
            val_dic["firstrun"] = ''
            val_dic["secondrun"] = ''

        if val_dic["firstdate"] and val_dic["secondate"] != '':
            val_dic["firstdate"] = dateconversions(val_dic["firstdate"])
            val_dic["secondate"] = dateconversions(val_dic["secondate"])
        print('radio: ' +str(val_dic["radio"]))
        print("firstdate : "+str(val_dic["firstdate"]))
        print("secondate : "+str(val_dic["secondate"]))
        print("firstrun : "+str(val_dic["firstrun"]))
        print("secondrun : "+str(val_dic["secondrun"]))
        print("object_ : "+str(val_dic["radio_obj"]))
        print("avg_all : "+str(val_dic["radio_all_avg"]))
        ################################ call functions from alkis.py ###############################
        connect_to_database()

        if val_dic["radio"] == "all":
            print('all')
            plotswithplotly(val_dic["radio_obj"] , val_dic["radio_all_avg"])
        elif val_dic["radio"] == "sp_date":
            print('per date')
            plots_with_specific_date_input(val_dic["firstdate"], val_dic["secondate"], val_dic["radio_obj"], val_dic["radio_all_avg"])
        elif val_dic["radio"] == "sp_run":
            print('per run')
            plots_with_specific_run_input(val_dic["firstrun"], val_dic["secondrun"], val_dic["radio_all_avg"], val_dic["radio_obj"])

        return json.dumps({'status':'OK'});
    return 

@app.route('/available_dates.html')
def available_dates():
    connect_to_database()
    get_run_counter()
    keys_values_lists()
    counters = get_run_counter()
    keys_values = keys_values_lists()
    return render_template('available_dates.html', datadates=keys_values["v_available_dates"])

@app.route('/available_runs.html')
def available_runs():
    connect_to_database()
    get_run_counter()
    keys_values_lists()
    counters = get_run_counter()
    keys_values = keys_values_lists()
    return render_template('available_runs.html', dataruns=counters["counterlistnums"])


@app.route('/plot.html')
def plot():
    try:
        ###################### output file name for specific run range #############################
        if val_dic["firstrun"] != '' and val_dic["secondrun"] != '':
            output = '/plots/' + str(val_dic["firstrun"]) + '_' + str(val_dic["secondrun"]) + val_dic["radio_obj"] + val_dic["radio_all_avg"] + '.html'


        ###################### output file name for specific date range #############################
        elif val_dic["firstdate"] != '' and val_dic["secondate"] != '':
            newfirstdate = val_dic["firstdate"].replace(" ","_")
            newlastdate = val_dic["secondate"].replace(" ","_")
            output = '/plots/' + newfirstdate + '_' + newlastdate + val_dic["radio_obj"] + val_dic["radio_all_avg"] + '.html'


        ########################## output file name for all runs ################################
        else:
            output = '/plots/' + val_dic["radio"] + val_dic["radio_obj"] + val_dic["radio_all_avg"] + '.html'

        return render_template(output)
    except:
        connect_to_database()
        get_run_counter()
        keys_values_lists()
        counters = get_run_counter()
        keys_values = keys_values_lists()

        return render_template('fail_input_on_plots.html', dataruns=counters["counterlistnums"], datadates=keys_values["v_available_dates"])





###########
# ########################################################## PLOTS WITH PLOTLY LIB ##########################################################################
##########
#######
# ############################################################ ALL RUNS PLOTS ####################################################################
######
def plotswithplotly(where,what):
    try:
        #Check for Bad Input
        valid_args_what = [
            'avg',
            'all'
        ]

        valid_args_where = [
            'total_free_memory',
            'mem_usage',
            'cpu_usage',
            'vmem_usage',
            'errors'
        ]

        if what not in valid_args_what and where not in valid_args_where:
             raise Exception('Bad input')
             return

        keys_values = keys_values_lists()
        counters = get_run_counter()

        ########################################## Input Validation ######################################
        if what == 'avg':
            xlabel = counters["counterlistnums"]
            ylabel = averagevalues(where)

        elif what == 'all':
            if where == 'total_free_memory':
                    xlabel = keys_values["k_total_free_memory"]
                    ylabel = keys_values["v_total_free_memory"]

            elif where == 'mem_usage':
                    xlabel = keys_values["k_mem_usage"]
                    ylabel = keys_values["v_mem_usage"]

            elif where == 'cpu_usage':
                    xlabel = keys_values["k_cpu_usage"]
                    ylabel = keys_values["v_cpu_usage"]

            elif where == 'vmem_usage':
                    xlabel = keys_values["k_vmem_usage"]
                    ylabel = keys_values["v_vmem_usage"]

            elif where == 'errors':
                    xlabel = keys_values["k_errors"]
                    ylabel = keys_values["v_errors"]


        plotname = 'all'+where+what+'.html'

        ########################################## Create Plot ##############################
        trace = go.Scatter(
            x=xlabel,
            y=ylabel,
            name = "plotswithplotly"
        )
        fig = tools.make_subplots(rows=1, cols=1)
        fig.append_trace(trace, 1,1)
        fig['layout'].update(title='')
        remove_command = "rm /root/project/templates/plots/"+plotname # remove old .html
        os.system(remove_command)
        plotly.offline.plot(fig, filename=plotname)
        copy_command = 'cp {} ./templates/plots'.format(plotname) #cp file to the right directory
        os.system(copy_command)
        remove_first_html_command = "rm /root/project/"+plotname
        os.system(remove_first_html_command)

    except UnboundLocalError as e:
        print ('Error from the plots_with_specific_run_input')
        print(e)

#######
############################################################ PLOTS FOR SPECIFIC RUNS #############################################################
#######

def plots_with_specific_run_input(first,last,what,where):
    #Check for Bad Input
    valid_args_what = [
        'avg',
        'all'
    ]

    valid_args_where = [
        'total_free_memory',
        'mem_usage',
        'cpu_usage',
        'vmem_usage',
        'errors'
    ]

    if what not in valid_args_what and where not in valid_args_where:
         raise Exception('Bad input')
         return

    try:
        keys_values = keys_values_lists()

        title = ''
        title = keys_values["v_stats"][int(first)-1].replace(' ',' ')

        plotname = str(first)+'_'+str(last)+where+what+'.html'

        if what=='all':
            ylabel = specific_runs(first,last,what,where)
            xlabel = []
            for i in range(1,len(ylabel)+1):
                xlabel.append(i)

            trace = go.Scatter(
                x=xlabel,
                y=ylabel,
                name = "all_per_run"
            )
            fig = tools.make_subplots(rows=1, cols=1)
            fig.append_trace(trace, 1,1)
            if first==last:
                fig['layout'].update(title=go.layout.Title(text=title, font=dict(size = 10,color='#7f7f7f')))
            else:
                fig['layout'].update(title='')
            remove_command = "rm /root/project/templates/plots/"+plotname
            os.system(remove_command)
            plotly.offline.plot(fig, filename=plotname)
            copy_command = 'cp {} ./templates/plots'.format(plotname)
            os.system(copy_command)
            remove_first_html_command = "rm /root/project/"+plotname
            os.system(remove_first_html_command)


        elif what=='avg':
            xlabel,ylabel = specific_runs(first,last,what,where)
            trace = go.Scatter(
                x=xlabel,
                y=ylabel,
                name = "avg_per_run"
            )
            fig = tools.make_subplots(rows=1, cols=1)
            fig.append_trace(trace, 1,1)
            if first==last:
                fig['layout'].update(title=go.layout.Title(text=title, font=dict(size = 10,color='#7f7f7f')))
            else:
                fig['layout'].update(title='')
            remove_command = "rm /root/project/templates/plots/"+plotname
            os.system(remove_command)
            plotly.offline.plot(fig, filename=plotname)
            copy_command = 'cp {} ./templates/plots'.format(plotname)
            os.system(copy_command)
            remove_first_html_command = "rm /root/project/"+plotname
            os.system(remove_first_html_command)

    except (IndexError,ValueError,UnboundLocalError) as e:
        print('Error from the plots_with_specific_run_input')
        print(e)

#######
############################################################ PLOTS FOR SPECIFIC DATE #############################################################
#######

def plots_with_specific_date_input(first,last,where,what):
    #Check for Bad Input
    valid_args_what = [
        'avg',
        'all'
    ]

    valid_args_where = [
        'total_free_memory',
        'mem_usage',
        'cpu_usage',
        'vmem_usage',
        'errors'
    ]

    if what not in valid_args_what and where not in valid_args_where:
         raise Exception('Bad input')
         return

    try:
        newfirst= first.replace(" ","_")
        newlast = last.replace(" ","_")
        plotname = newfirst+'_'+newlast+where+what+'.html'

        # ######################################## all ########################################
        if what == 'all':
            xlabel,ylabel = specific_date(first,last,where)
            trace = go.Scatter(
                x=xlabel,
                y=ylabel,
                name = "all_spec_date"
            )
            fig = tools.make_subplots(rows=1, cols=1)
            fig.append_trace(trace, 1,1)
            fig['layout'].update(title='')
            remove_command = "rm /root/project/templates/plots/"+plotname
            os.system(remove_command)
            plotly.offline.plot(fig, filename=plotname)
            copy_command = 'cp {} ./templates/plots'.format(plotname)
            os.system(copy_command)
            remove_first_html_command = "rm /root/project/"+plotname
            os.system(remove_first_html_command)

        # ######################################## avg ########################################
        elif what == 'avg':
            xlabel,ylabel = date_calculator(first,last,where)
            trace = go.Scatter(
                x=xlabel,
                y=ylabel,
                name = "avg_spec_date"
            )
            fig = tools.make_subplots(rows=1, cols=1)
            fig.append_trace(trace, 1,1)
            fig['layout'].update(title='')
            remove_command = "rm /root/project/templates/plots/"+plotname
            os.system(remove_command)
            plotly.offline.plot(fig, filename=plotname)
            copy_command = 'cp {} ./templates/plots'.format(plotname)
            os.system(copy_command)
            remove_first_html_command = "rm /root/project/"+plotname
            os.system(remove_first_html_command)

    except (UnboundLocalError , TypeError) as e:
        print('Error from plots_with_specific_date_input')
        print(e)


if __name__ == "__main__":
    app.run(host=host_address)


