import time
import hashlib
# Use Cloudant to create a Cloudant client using account4
from cloudant.account import Cloudant
import os
from flask import Flask, Response
from flask import request
import json
from flask_table import Table, Col

#Connectiong to Cloudant DB
USERNAME = '9afad61c-3164-4f7c-84e6-efefd9b3294c-bluemix'
PASSWORD = '8b5132e99c4cd6a826f7a8a1230dfe9f7efbe99245620e2954bd007ac1df6fd8'
Account_name='9afad61c-3164-4f7c-84e6-efefd9b3294c-bluemix:8b5132e99c4cd6a826f7a8a1230dfe9f7efbe99245620e2954bd007ac1df6fd8@9afad61c-3164-4f7c-84e6-efefd9b3294c-bluemix'
client = Cloudant(USERNAME, PASSWORD, account=Account_name)
client.connect()
my_database = client['my_database']

app = Flask(__name__)
# UPLOAD_FOLDER = '/home/laevo'
# ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/')
def Welcome():
    return app.send_static_file('index.html')

# def allowed_file(filename):
#     return '.' in filename and \
#            filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

# Declare your table
class ItemTable(Table):
    name = Col('FIlename')
    version = Col('Version')
    last_modified = Col('Last Modified Date')
# Get some objects
class Item(object):
    def __init__(self, name, version, last_modified):
        self.name = name
        self.version = version
        self.last_modified = last_modified
items = []
for document in my_database:
    try:
        doc = [Item(document['file_name'], document['version'], document['last_modified_date'])]
        items = items + doc
    except KeyError:
        pass
table = ItemTable(items)
passtable = (table.__html__())


@app.route('/list', methods=['GET', 'POST'])
def list_files():
    if request.method == 'GET':
        return passtable


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file :
            file_name = file.filename
            content = file.read()
            hashfunc = hashlib.md5()
            hashfunc.update(content)
            hash_val = (hashfunc.hexdigest())
            timenow = time.strftime("%c")
            exist_flag = 0
            for document in my_database:
                if document['file_name'] == file_name:
                    exist_flag = 1
                    l_version = document['version']
                    for document in my_database:
                        if document['file_name'] == file_name:
                            if document['version'] > l_version:
                                l_version = document['version']
            for document in my_database:
                if document['file_name'] == file_name and document['version'] == l_version:
                    print 'File already present, checking contents...'
                    if document['hash'] == hash_val:
                        print 'Warning: Duplicate file'
                        return 'Warning: Duplicate file'
                        break
                    else:
                        version = document['version']
                        data = {
                            'file_name': file_name,
                            'hash': hash_val,
                            'version': version+1,
                            'last_modified_date': str(timenow),
                            'contents': content
                            }
                        my_document = my_database.create_document(data)
                        return 'Contents different. New version inserted'
                elif exist_flag == 0:
                    data = {
                        'file_name': file_name,
                        'hash': hash_val,
                        'version': 1,
                        'last_modified_date': str(timenow),
                        'contents': content
                        }
                    my_document = my_database.create_document(data)
                    return 'New document inserted'
                    break
    return app.send_static_file('index.html')


@app.route('/delete', methods=['GET', 'POST'])
def delete_file():
    if request.method == 'POST':
        filename = request.form['filename']
        fileversion = request.form['fileversion']
        for document in my_database:
            if filename == document['file_name'] and str(fileversion) == str(document['version']):
                document.delete()
                return 'File Deleted'
                break
    return 'File Not Found'

@app.route('/download', methods=['GET', 'POST'])
def download_file():
    if request.method == 'POST':
        filename = request.form['filename']
        fileversion = request.form['fileversion']
        for document in my_database:
            if filename == document['file_name'] and str(fileversion) == str(document['version']):
                new_doc = open(str(document['file_name']), 'wb')
                new_doc.write(str(document['contents']))
                return 'File Downloaded'
                break
    return 'File Not Found'

port = os.getenv('VCAP_APP_PORT', '5001')
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(port), debug=True)
