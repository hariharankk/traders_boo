from flask import Flask, jsonify, request
import json
from dateutil.relativedelta import relativedelta
import datetime
import copy
import time
import credentials
import redis
from flask_cors import CORS

class data_modification(object):
  def __init__(self):
    self.host , self.password , self.port = credentials.load_correct_creds()
    self.client = redis.StrictRedis(host = self.host , port=self.port, password = self.password , decode_responses=True) 
    self.nifty_oi_data = json.loads(self.client.json().get("options_data"))
    self.expiryDates= self.expiry_data()
  
  def expiry_data(self):
      expiryDates = self.nifty_oi_data['records']['expiryDates']
      return  expiryDates
      
  def modify_data(self):
        date_format=[]
        threshold = datetime.datetime.combine(datetime.date.today() + relativedelta(months=+3), datetime.time(0, 0))
        for i in range(len(self.expiryDates)):
            dummy=datetime.datetime.strptime(self.expiryDates[i], "%d-%b-%Y")
            if dummy < threshold:
              date_format.append(dummy.strftime('%d-%b-%Y'))
        return date_format  

  def get_optionchain_data(self , date):
        return_data={}
        for i in range(len(self.nifty_oi_data['records']['data'])):
          if datetime.datetime.strptime(self.nifty_oi_data['records']['data'][i]['expiryDate'], "%d-%b-%Y") == datetime.datetime.strptime(date, "%d-%b-%Y"):
            strike_price=str(self.nifty_oi_data['records']['data'][i]['strikePrice'])
            data=copy.deepcopy(self.nifty_oi_data['records']['data'][i])
            del data['strikePrice']
            del data['expiryDate']
            return_data[strike_price]=data
        return return_data    



app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
   

@app.route("/api/exirpyDates", methods=["GET"])
def expiry_date():  
    data_obj = data_modification()
    expiryDates = data_obj.modify_data()
    return jsonify({'expiryDates': expiryDates})



@app.route("/api/optionChain", methods=["GET"])
def option_data():
      data_obj = data_modification()
      args = request.args
      date = args.get('expiry') 
      data = data_obj.get_optionchain_data(date)
      return data



