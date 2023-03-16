import mysql.connector
from flask import Flask, request, jsonify
import os
import uuid
import barcode
from barcode.writer import ImageWriter
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib

# Create the Flask app
app = Flask(__name__)

# Connect to the database
db = mysql.connector.connect(
  host="db5012315885.hosting-data.io",
  user="dbu2006945",
  password="TenWolfMadCar1!",
  database="dbs10360416",
)

mycursor = db.cursor()

app = Flask(__name__)

@app.route('/create_user', methods=['POST'])
def create_user():
    # Get user input from request body
    name = request.json['name']
    email = request.json['email']
    amnt = request.json['amnt']
    
    # Create temporary directory for barcode images
    os.makedirs("temp", exist_ok=True)
    
    # Set up email message
    msg = MIMEMultipart()
    msg['From'] = 'jeld.ticketingservice@gmail.com'
    msg['To'] = email
    msg['Subject'] = 'Ticket Purchase Code'
    
    # Add text to the message
    text = MIMEText("Hello " + name + "!" + ' I have attached your code to enter the site!')
    msg.attach(text)

    # Generate barcode and insert user into database for each ticket purchased
    for i in range(int(amnt)):
        bcodeInfo = str(uuid.uuid4().hex)[:16]
        
        # Insert the new user into the database
        # You need to replace the placeholders (%s) with actual values and set up your database connection
        sql = "INSERT INTO users (name, barcode, email) VALUES (%s, %s, %s)"
        val = (name, bcodeInfo, email)
        mycursor.execute(sql, val)
        db.commit()
        
        # Generate barcode image
        EAN = barcode.get_barcode_class('code128')
        ean = EAN(bcodeInfo, writer=ImageWriter())
        ean.save('temp/barcode')
        
        # Attach barcode image to email message
        path = 'temp/barcode.png'
        with open(path, 'rb') as f:
            img_data = f.read()
            img = MIMEImage(img_data, name=os.path.basename(path))
            msg.attach(img)

    # Send the email
    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login('jeld.ticketingservice@gmail.com', 'qfgowrwruolqbqky')
        smtp.send_message(msg)

    # Remove temporary files and directory
    for file_name in os.listdir("temp"):
        if os.path.isfile(os.path.join("temp", file_name)):
                    os.remove(os.path.join("temp", file_name))
    os.rmdir("temp")
    
    # Return success message
    return jsonify({"message": "Guest created successfully"})

# Define the check_in API endpoint
@app.route('/check_in', methods=['POST'])
def check_in():
    # Get the barcode value from the request body
    barcode = request.json.get('barcode')
        
    mycursor = db.cursor()

    
    # Query the database for the barcode
    mycursor.execute("SELECT * FROM users WHERE barcode=%s", (barcode,))
    guest = mycursor.fetchone()
    
    mycursor.execute("SELECT name FROM users WHERE barcode = %s",(barcode,))
    existingName = mycursor.fetchone()

    # If the guest is not found, return an error message
    if guest is None:
        return jsonify({'message': 'Invalid barcode'}), 400
    
    # If the guest has already been checked in, return a message
    if guest[3] == True:
        return jsonify({'message': 'This guest has already been checked in', 'name': existingName[0]}), 200
    
    # Otherwise, update the guest's record in the database
    mycursor.execute("UPDATE users SET checked_in=True WHERE barcode=%s", (barcode,))
    db.commit()
    
    # Return a success message
    return jsonify({'message': 'Guest checked in successfully'}), 200

if __name__ == '__main__':
    app.run(debug=True)
