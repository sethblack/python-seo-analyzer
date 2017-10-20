from flask import Flask,render_template
import json

app = Flask(__name__)

@app.route('/')
def index():
	try:
		with open('output.json','r') as f:
			results = json.load(f)
			print(results)
	except FileNotFoundError:
		results = {'fatal_error':True}
	return render_template('index.html',result=results)

if __name__ == '__main__':
	app.run(debug = True)