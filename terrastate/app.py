#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import json
import errno
import time

from os.path import dirname
from os.path import join

from flask import Flask
from flask import request
from flask import jsonify
from flask.views import MethodView

from flask import Flask, request, redirect

from flask import Flask, request, redirect
import pymysql

from werkzeug.exceptions import default_exceptions
from werkzeug.exceptions import HTTPException


db_conn = pymysql.connect(user='root', passwd=None)
db_cursor = db_conn.cursor()
# Create the DB if it doesn't exist, then use it
db_cursor.execute('CREATE DATABASE IF NOT EXISTS terraform')
db_conn.select_db('terraform')

# Create the url tracking table. This is a table that has:
# - an `id` integer number that increments automatically
# - the creation time (as an integer, the same as python time.time() )
# - the url, as a 255 character long string
db_cursor.execute('''
CREATE TABLE IF NOT EXISTS statefiles (
   `id` INT AUTO_INCREMENT,
   `env` VARCHAR(255),
   `statefile` TEXT,
   PRIMARY KEY (id)
)
''')

db_conn.commit()

locked = False


# init:
# load({'serial': 0,
#     'version': 1,
#     'modules': [
#         {'path': ['root'],
#         'resources': {},
#         'outputs': {}}]}
# )
# 127.0.0.1 - - [22/Jul/2018 15:54:30] "GET /thinking_face HTTP/1.1" 200 -

# plan:
# save({
#     u'Info': u'',
#     u'Version': u'0.11.7',
#     u'Created': u'2018-07-22T19:54:41.657104783Z',
#     u'Who': u'jmeichle@jmeichle-Precision-5520',
#     'modules': [
#         {'path': ['root'],
#         'resources': {},
#         'outputs': {}}],
#     u'ID': u'a8383823-543f-d639-ab79-471f1bd3eacb',
#     'version': 1,
#     u'Path': u'',
#     'serial': 0,
#     u'Operation': u'OperationTypePlan'
# })
# Running query: INSERT INTO statefiles (created_time, statefile) VALUES (1, '{\"Info\": \"\", \"Version\": \"0.11.7\", \"Created\": \"2018-07-22T19:54:41.657104783Z\", \"Who\": \"jmeichle@jmeichle-Precision-5520\", \"modules\": [{\"path\": [\"root\"], \"resources\": {}, \"outputs\": {}}], \"ID\": \"a8383823-543f-d639-ab79-471f1bd3eacb\", \"version\": 1, \"Path\": \"\", \"serial\": 0, \"Operation\": \"OperationTypePlan\"}')
# 127.0.0.1 - - [22/Jul/2018 15:54:41] "POST /lock HTTP/1.1" 200 -
# load({
#     'serial': 0,
#     'version': 1,
#     'modules': [
#         {'path': ['root'],
#         'resources': {},
#         'outputs': {}}
#     ]
# })
# 127.0.0.1 - - [22/Jul/2018 15:54:41] "GET /thinking_face HTTP/1.1" 200 -
# destroy({
#     u'Info': u'',
#     u'Version': u'0.11.7',
#     u'Created': u'2018-07-22T19:54:41.657104783Z',
#     u'Who': u'jmeichle@jmeichle-Precision-5520',
#     'modules': [
#         {'path': ['root'],
#         'resources': {},
#         'outputs': {}}],
#     u'ID': u'a8383823-543f-d639-ab79-471f1bd3eacb',
#     'version': 1,
#     u'Path': u'',
#     'serial': 0,
#     u'Operation': u'OperationTypePlan'
# })
# Running query: DELETE FROM statefiles WHERE created_time=1
# 127.0.0.1 - - [22/Jul/2018 15:54:41] "DELETE /lock HTTP/1.1" 200 -


# apply:
# save({u'Info': u'',
#       u'Version': u'0.11.7',
#       u'Created': u'2018-07-22T19:54:51.546704608Z',
#       u'Who': u'jmeichle@jmeichle-Precision-5520',
#       'modules': [
#         {'path': ['root'],
#           'resources': {},
#           'outputs': {}}],
#       u'ID': u'e5e55302-23fb-f767-1b27-8260dc7c4298',
#       'version': 1,
#       u'Path': u'',
#       'serial': 0,
#       u'Operation': u'OperationTypeApply'
# })
# Running query: INSERT INTO statefiles (created_time,
#     statefile) VALUES (1, '{\"Info\": \"\", \"Version\": \"0.11.7\", \"Created\": \"2018-07-22T19:54:51.546704608Z\", \"Who\": \"jmeichle@jmeichle-Precision-5520\", \"modules\": [{\"path\": [\"root\"], \"resources\": {}, \"outputs\": {}}], \"ID\": \"e5e55302-23fb-f767-1b27-8260dc7c4298\", \"version\": 1, \"Path\": \"\", \"serial\": 0, \"Operation\": \"OperationTypeApply\"}')
# 127.0.0.1 - - [22/Jul/2018 15:54:51] "POST /lock HTTP/1.1" 200 -
# load({'serial': 0, 'version': 1, 'modules': [{'path': ['root'], 'resources': {}, 'outputs': {}}]})
# 127.0.0.1 - - [22/Jul/2018 15:54:51] "GET /thinking_face HTTP/1.1" 200 -
   

#    # mysql> select * from statefiles\G
#    # *************************** 1. row ***************************
#    #           id: 38
#    # created_time: 1
#    #    statefile: {
#    #                  "Info": "",
#    #                  "Version": "0.11.7",
#    #                  "Created": "2018-07-22T19:54:51.546704608Z",
#    #                  "Who": "jmeichle@jmeichle-Precision-5520",
#    #                  "modules": [{"path": ["root"],
#    #                  "resources": {},
#    #                  "outputs": {}}],
#    #                  "ID": "e5e55302-23fb-f767-1b27-8260dc7c4298",
#    #                  "version": 1,
#    #                  "Path": "",
#    #                  "serial": 0,
#    #                  "Operation": "OperationTypeApply"
#    #                }
#    # 1 row in set (0.00 sec)



# yes:
# save({
#     u'lineage': u'23022e6d-b7f5-b6c8-d523-6bb3219de896',
#     u'terraform_version': u'0.11.7',
#     'modules': [
#         {u'path': [u'root'],
#         u'depends_on': [],
#         u'resources': {u'local_file.hmm': {u'depends_on': [],
#         u'provider': u'provider.local',
#         u'type': u'local_file',
#         u'primary': {
#          u'attributes': {
#           u'content':
#            u'hmm!',
#            u'id': u'0af43cd25f0a79e365b4637178af50e748a9b406',
#            u'filename': u'/home/jmeichle/projects/2018-07-22/test_tf_http_state_data_provider/hmm.bar'},
#            u'meta': {},
#            u'tainted': False,
#            u'id': u'0af43cd25f0a79e365b4637178af50e748a9b406'},
#            u'deposed': []
#           }
#          },
#          u'outputs': {}
#     }],
#     'version': 3, 'serial': 2
# })
# Running query: INSERT INTO statefiles (created_time, statefile) VALUES (1, '{\"lineage\": \"23022e6d-b7f5-b6c8-d523-6bb3219de896\", \"terraform_version\": \"0.11.7\", \"modules\": [{\"path\": [\"root\"], \"depends_on\": [], \"resources\": {\"local_file.hmm\": {\"depends_on\": [], \"provider\": \"provider.local\", \"type\": \"local_file\", \"primary\": {\"attributes\": {\"content\": \"hmm!\", \"id\": \"0af43cd25f0a79e365b4637178af50e748a9b406\", \"filename\": \"/home/jmeichle/projects/2018-07-22/test_tf_http_state_data_provider/hmm.bar\"}, \"meta\": {}, \"tainted\": false, \"id\": \"0af43cd25f0a79e365b4637178af50e748a9b406\"}, \"deposed\": []}}, \"outputs\": {}}], \"version\": 3, \"serial\": 2}')
# 127.0.0.1 - - [22/Jul/2018 15:55:00] "POST /thinking_face?ID=e5e55302-23fb-f767-1b27-8260dc7c4298 HTTP/1.1" 200 -
# destroy({
#     u'Info': u'',
#     u'Version': u'0.11.7',
#     u'Created': u'2018-07-22T19:54:51.546704608Z',
#     u'Who': u'jmeichle@jmeichle-Precision-5520',
#     'modules': [
#         {'path': ['root'],
#         'resources': {},
#         'outputs': {}}
#     ],
#     u'ID': u'e5e55302-23fb-f767-1b27-8260dc7c4298',
#     'version': 1,
#     u'Path': u'',
#     'serial': 0,
#     u'Operation': u'OperationTypeApply'})
# Running query: DELETE FROM statefiles WHERE created_time=1
# 127.0.0.1 - - [22/Jul/2018 15:55:00] "DELETE /lock HTTP/1.1" 200 -

class MysqlBasedTerraformState(dict):
    """Representation of a Terraform statefile"""

    def __init__(self, config):
        dict.__init__(self)
        self.env = None
        self.config = config
        self.update({
            'version': 1,
            'serial': 0,
            'modules': [{
                'path': ['root'],
                'outputs': {},
                'resources': {}
            }]
        })

    def load(self):
        the_cursor = db_conn.cursor(pymysql.cursors.DictCursor)
        env = db_conn.escape(self.env)
        the_cursor.execute("SELECT * FROM statefiles WHERE env={}".format(env))
        # Iterate each row
        for row in the_cursor:
            print "Reading {}".format('DB row env={}'.format(self.env))
            self.update(json.loads(row['statefile']))
        else:
            print "{} Not Found".format('DB row env={}'.format(self.env))
            return

    def save(self):
        the_cursor = db_conn.cursor(pymysql.cursors.DictCursor)
        env = db_conn.escape(self.env)
        the_cursor.execute("SELECT * FROM statefiles WHERE env={}".format(env))
        # Iterate each row
        for row in the_cursor:
            data = db_conn.escape(json.dumps(self))
            query = "UPDATE statefiles SET statefile = {} WHERE env={}".format(data, env)
            print 'Updating DB: {}'.format(query)
            the_cursor.execute(query)
            break
        else:
            data = db_conn.escape(json.dumps(self))
            query = "INSERT INTO statefiles (env, statefile) VALUES ({}, {})".format(env, data)
            print 'Creating DB: {}'.format(query)
            the_cursor.execute(query)
        db_conn.commit()

    def destroy(self):
        the_cursor = db_conn.cursor(pymysql.cursors.DictCursor)
        env = db_conn.escape(self.env)
        print "Deleting DB record env={} UH".format(env)
        the_cursor.execute("DELETE FROM statefiles WHERE env={}".format(env))
        db_conn.commit()

    def lock(self):
        print('lock({})'.format(self, indent=4, sort_keys=True))
        print('  OPERATION ID: {}'.format(self.get('Operation', '')))

    def unlock(self):
        print('unlock({})'.format(self, indent=4, sort_keys=True))
        print('  OPERATION ID: {}'.format(self.get('Operation', '')))


# class FileBasedTerraformState(dict):
#     """Representation of a Terraform statefile"""

#     def __init__(self, config):
#         dict.__init__(self)
#         self.env = None
#         self.config = config
#         self.statepath = self._mkstatedir(config['statepath'])
#         self.update({
#             'version': 1,
#             'serial': 0,
#             'modules': [{
#                 'path': ['root'],
#                 'outputs': {},
#                 'resources': {}
#             }]
#         })

#     def _mkstatedir(self, statepath):
#         try:
#             os.makedirs(statepath, mode=0o744)
#         except OSError as err:
#             if err.errno == errno.EEXIST and os.path.isdir(statepath):
#                 pass
#             else:
#                 raise
#         return statepath

#     def _getstatefilename(self, env):
#         return os.path.join(self.statepath, '%s-tfstate.json' % (env, ))

#     def _getlockfilename(self, env):
#         return os.path.join(self.statepath, '%s-tfstate.lock' % (env, ))

#     def load(self):
#         filename = self._getstatefilename(self.env)
#         if not os.path.isfile(filename):
#             print "{} Not Found".format(filename)
#             return
#         with open(filename) as fh:
#             print "Reading {}".format(filename)
#             self.update(json.load(fh))

#     def save(self):
#         filename = self._getstatefilename(self.env)
#         print "Writing to {}".format(filename)
#         with open(filename, 'w+') as fh:
#             json.dump(self, fh, indent=2)

#     def destroy(self):
#         filename = self._getstatefilename(self.env)
#         print "Deleting {}".format(filename)
#         if os.path.isfile(filename):
#             os.unlink(filename)

#     def lock(self):
#         if os.path.isfile(self._getlockfilename(self.env)):
#             raise Exception('Already locked')
#         with open(self._getlockfilename(self.env), 'w') as fh:
#             fh.write('locked')

#     def unlock(self):
#         if os.path.isfile(self._getlockfilename(self.env)):
#             os.unlink(self._getlockfilename(self.env))
#         else:
#             raise Exception('Not locked')


class Config(dict):
    """A simple json config file loader

    :param str filename: path to the json file
    """
    def __init__(self, filename):
        dict.__init__(self)
        self.update(json.load(open(filename)))


class StateView(MethodView):
    """Terraform State MethodView"""

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)
        self.config = Config(join(dirname(__file__), 'config.json'))
        # self.state = FileBasedTerraformState(self.config)
        self.state = MysqlBasedTerraformState(self.config)

    def get(self, env):
        self.state.env = env
        self.state.load()
        return jsonify(self.state)

    def post(self, env):
        self.state.env = env
        self.state.update(request.get_json())
        self.state.save()
        return jsonify(self.state)

    def delete(self, env):
        self.state.env = env
        self.state.update(request.get_json())
        self.state.destroy()
        return jsonify(self.state)

    def lock(self, env):
        self.state.env = env
        self.state.lock()
        self.state.load()
        return jsonify(self.state)

    def unlock(self, env):
        self.state.env = env
        self.state.unlock()
        self.state.load()
        return jsonify(self.state)


class TerraStateApi(Flask):
    def __init__(self, name):
        Flask.__init__(self, name)

        dhc_view = StateView.as_view('status')
        self.add_url_rule('/', defaults={'env': None}, view_func=dhc_view)
        self.add_url_rule('/<env>', view_func=dhc_view, methods=['GET', 'POST', 'DELETE', 'LOCK', 'UNLOCK'])

        # add custom error handler
        for code in default_exceptions.iterkeys():
            self.register_error_handler(code, self.make_json_error)

    def make_json_error(self, ex):
        if isinstance(ex, HTTPException):
            code = ex.code
            message = ex.description
        else:
            code = 500
            message = str(ex)

        response = jsonify(code=code, message=message)
        response.status_code = code

        return response


app = TerraStateApi(__name__)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
