from flask import Flask, render_template, jsonify, redirect
import baserow

app = Flask(__name__)

@app.route('/')
def home():
    reqs = baserow.get_requests()
    return render_template('index.html', requests=sorted(list(reqs.values()), key=lambda x: x['dept']['Name'].lower()))

@app.route("/request/<req>")
def department(req):
    request = baserow.get_request(req)
    sections = baserow.get_sections(request)
    return render_template("request.html", request=request, sections=sections)

@app.route("/checkout/<table>/<item>", methods=["POST"])
def checkout_item(table, item):
    print(f"Checking out item {item} from {table}")
    baserow.update_status(table, item, "Picked Up")
    return jsonify({})

@app.route("/checkin/<table>/<item>", methods=["POST"])
def checkin_item(table, item):
    print(f"Checking in item {item} from {table}")
    baserow.update_status(table, item, "Returned")
    return jsonify({})

@app.route("/checkout/<request>", methods=["POST"])
def checkout_all(request):
    print(f"Checking out whole request {request}")
    baserow.update_request_status(baserow.get_request(request), "Picked Up")
    return redirect(f"/request/{request}", code=302)

@app.route("/checkin/<request>", methods=["POST"])
def checkin_all(request):
    print(f"Checking in whole request {request}")
    baserow.update_request_status(baserow.get_request(request), "Returned")
    return redirect(f"/request/{request}", code=302)

if __name__ == "__main__":
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.jinja_env.cache = None
    app.run(debug=True)