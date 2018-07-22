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


class FileBasedTerraformState(dict):
    """Representation of a Terraform statefile"""

    def __init__(self, config):
        dict.__init__(self)
        self.env = None
        self.config = config
        self.statepath = self._mkstatedir(config['statepath'])
        self.update({
            'version': 1,
            'serial': 0,
            'modules': [{
                'path': ['root'],
                'outputs': {},
                'resources': {}
            }]
        })

    def _mkstatedir(self, statepath):
        try:
            os.makedirs(statepath, mode=0o744)
        except OSError as err:
            if err.errno == errno.EEXIST and os.path.isdir(statepath):
                pass
            else:
                raise
        return statepath

    def _getstatefilename(self, env):
        return os.path.join(self.statepath, '%s-tfstate.json' % (env, ))

    def _getlockfilename(self, env):
        return os.path.join(self.statepath, '%s-tfstate.lock' % (env, ))

    def load(self):
        filename = self._getstatefilename(self.env)
        if not os.path.isfile(filename):
            print "{} Not Found".format(filename)
            return
        with open(filename) as fh:
            print "Reading {}".format(filename)
            self.update(json.load(fh))

    def save(self):
        filename = self._getstatefilename(self.env)
        print "Writing to {}".format(filename)
        with open(filename, 'w+') as fh:
            json.dump(self, fh, indent=2)

    def destroy(self):
        filename = self._getstatefilename(self.env)
        print "Deleting {}".format(filename)
        if os.path.isfile(filename):
            os.unlink(filename)

    def lock(self):
        if os.path.isfile(self._getlockfilename(self.env)):
            raise Exception('Already locked')
        with open(self._getlockfilename(self.env), 'w') as fh:
            fh.write('locked')

    def unlock(self):
        if os.path.isfile(self._getlockfilename(self.env)):
            os.unlink(self._getlockfilename(self.env))
        else:
            raise Exception('Not locked')


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
