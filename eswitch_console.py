#!/usr/local/bin/python
#encoding: utf-8

import web
from web import SQLLiteral as sql
from web.contrib.template import render_jinja

import math
import json
import threading
import requests
from datetime import datetime
from datetime import timedelta

from eswitch_settings import *

class JsonEncoderX(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)

urls = (
    # web
    '/',                        'app_list',
    '/login',                   'login',
    '/app/list',                'app_list',
    '/app/add',                 'app_add',
    '/item/list/(\d+)',         'item_list',
    '/item/list/(\d+)-(\d+)',   'item_list',
    '/item/add/(\d+)',          'item_add',
    '/item/update/(\d+)',       'item_update',
    '/instance/list/(\d+)',     'instance_list',
    # api
    '/register.json',           'api_instance_register',
    '/unregister.json',         'api_instance_unregister',
    '/keepalive.json',          'api_instance_keepalive',
    '/listItems.json',          'api_item_list',
)

# web
class index:
    def GET(self):
        return 'Welcome ESwitch Console.'

class login:
    def GET(self):
        return render.login()

    def POST(self):
        i = web.input()
        name, password = i['name'], i['password']
        resp = requests.get(sso_login, {
                'loginName' : name,
                'password'  : password,
            })
        if resp.status_code == 200 and resp.json()['success']:
            session.authed = True
            session.name = name
            web.seeother('/')
        else:
            errors = {'Msg' : 'user name or password is invalid.'}
            return render.login(errors=errors)

class app_list:
    def GET(self):
        apps = list(db.select('application'))
        return render.app_list(apps=apps)

class app_add:
    def GET(self):
        return render.app_add()

    def POST(self):
        i = web.input()
        if i['name'] == None or i['name'].strip() == '':
            return render.app_add(errors = {
                    'name'    :   'application\'s name is invalid.',
                })
        vars = {
            'name' : i['name']
        }
        if len(db.select('application', vars, where='name = $name')) > 0:
            return render.app_add(errors = {
                    'name'    :   'application\'s name is duplicated.',
                })

        app = {
            'name'          : i['name'].strip(),
            'description'   : i['description'].strip(),
            'create_date'   : sql('now()'),
            'update_date'   : sql('now()'),
        }
        db.insert('application', **app)
        return web.seeother('/app/list')

class item_list:
    def GET(self, app_id, page='1'):
        vars = {
            'app_id'    : app_id,
        }
        apps = list(db.select('application', vars, where='id = $app_id'))
        app = apps[0] if len(apps) > 0 else None
        if not app:
            return render.item_list(app=app, items=[])

        total = db.select('item', vars, what='count(*) as total', where='app_id=$app_id')[0]['total']
        page = min(int(page), int(math.ceil(total / 10.0)))
        page = page if page > 0 else 1
        items = list(db.select('item', vars, where='app_id=$app_id', order='id desc', offset=(page-1) * 10, limit=10))
        pages = {
            'page'      : page,
            'page_max'  : int(math.ceil(total / 10.0)),
            'start'     : (page - 1) * 10 + 1 if total > 0 else 0,
            'end'       : int(min((page - 1) * 10 + 10, total)),
            'total'     : total,
        }
        return render.item_list(app=app, items=items, pages=pages)

class item_add:
    def GET(self, app_id):
        vars = {
            'app_id'    : app_id,
        }
        apps = list(db.select('application', vars, where='id = $app_id'))
        app = apps[0] if len(apps) > 0 else None
        return render.item_add(app_id=app_id, app=app)

    def POST(self, app_id):
        vars = {
            'app_id'    : app_id,
        }
        apps = list(db.select('application', vars, where='id = $app_id'))
        app = apps[0] if len(apps) > 0 else None
        if not app:
            return render.item_add(app_id=app_id, app=app)

        i = web.input()
        errors = {}
        if i['name'].strip() == '':
            errors['name'] = 'item\'s name is invalid.'
        if not i['on'] in ['0', '1']:
            errors['on'] = 'item\'s on is invalid.'
        if not i['threshold'].isdigit():
            errors['threshold'] = 'item\'s threshold is invliad.'
        if len(errors) > 0:
            return render.item_add(app_id=app_id, app=app, errors=errors)

        vars = {
            'name'  : i['name'],
        }
        if len(db.select('item', vars, where='name=$name')) > 0:
            errors['name'] = 'item\'s name is duplicated.'
            return render.item_add(app_id=app_id, app=app, errors=errors)

        item = {
            'app_id'        : app.id,
            'app_name'      : app.name,
            'name'          : i['name'].strip(),
            'description'   : i['description'].strip(),
            '`on`'          : int(i['on']),
            'threshold'     : int(i['threshold']),
            'detail'        : None,
            'create_date'   : sql('now()'),
            'update_date'   : sql('now()'),
        }
        db.insert('item', **item)
        return web.seeother('/item/list/%s' % (app_id))

class item_update:
    def GET(self, id):
        vars = {
            'id'    : id,
        }
        items = list(db.select('item', vars, where="id=$id"))
        item = items[0] if len(items) > 0 else None
        vars = {
            'item_id'       : id,
        }
        notifies = list(db.select('item_notify', vars=vars, where='item_id=$item_id'))
        notify = notifies[0] if len(notifies) > 0 else None
        if notify:
            notify['list'] = json.loads(notify['detail'])
        return render.item_update(id=id, item=item, notify=notify)

    def POST(self, id):
        i = web.input()
        errors={}
        if not i['on'] in ['0', '1']:
            errors['on'] = 'item\'s on is invalid.'
        if not i['threshold'].isdigit():
            errors['threshold'] = 'item\'s threshold is invliad.'
        if len(errors) > 0:
            return render.item_update(id=id, errors=errors, item=i)

        id = int(id)
        vars = {
            'id'    : id,
        }
        item = {
            'description'   : i['description'].strip(),
            '`on`'          : int(i['on']),
            'threshold'     : int(i['threshold']),
            'update_date'   : sql('now()'),
        }
        db.update('item', vars=vars, where='id=$id', **item)

        # async notify application instances
        r = db.select('item', vars=vars, where='id=$id')[0]
        def notify(r):
            vars = {
                'app_id'    : r.app_id,
                'last_ack'  : datetime.now() - timedelta(minutes=10)
            }
            instances = db.select('instance', vars=vars, where='app_id=$app_id and status=1 and last_ack > $last_ack')
            results = []
            for i in instances:
                url = 'http://%s:%s/eswitch/config' % (i.host, i.port)
                params = {
                    'action'    : 'modify',
                    'item'      : r.name,
                    r.name      : '{on:%s,threshold:%s}' % ('true' if r.on == 1 else 'false', r.threshold),
                }
                info = {
                    'host'      : i.host,
                    'port'      : i.port,
                    'status'    : False,
                }
                try:
                    resp = requests.get(url, params, timeout=3)
                    info['status'] = (resp.status_code == 200 and resp.json()['code'] == 200)
                except Exception as e:
                    info['status'] = False
                    print str(e)
                results.append(info)
            vars = {
                'item_id'       : r.id,
            }
            status_set = set([i['status'] for i in results])
            status = 2 if len(status_set) == 2 else \
                    (0 if False in status_set else 1)
            notifies = list(db.select('item_notify', vars=vars, where='item_id=$item_id'))
            if len(notifies) == 0:
                notify = {
                    'item_id'       : r.id,
                    'status'        : status,
                    'detail'        : json.dumps(results),
                    'create_date'   : sql('now()'),
                    'update_date'   : sql('now()'),
                }
                db.insert('item_notify', **notify)
            else:
                db.update('item_notify', vars=vars, where='item_id=$item_id',
                        status=status, detail=json.dumps(results), update_date=sql('now()'))

        threading.Thread(target=notify, args=(r,)).start()

        return web.seeother('/item/update/%d' % (id))

class instance_list:
    def GET(self, app_id):
        vars = {
            'app_id'    : app_id,
        }
        apps = list(db.select('application', vars, where='id = $app_id'))
        app = apps[0] if len(apps) > 0 else None
        if not app:
            return render.instance_list(app=app, instances=[])

        instances = list(db.select('instance', vars, where='app_id=$app_id'))
        for i in instances:
            if datetime.now() - timedelta(minutes=10) > i.last_ack:
                i.status = 2    # timeout
        return render.instance_list(app=app, instances=instances)


# api
class api_instance_register:
    def GET(self):
        i = web.input()
        web.header('Content-Type', 'application/json')
        r = {
            'success':  False,
            'data':     None,
        }

        if not i['app'] or i['app'].strip() == '':
            return json.dumps(r)
        if not i['port'] or not i['port'].isdigit():
            return json.dumps(r)

        vars = {
            'name'  : i['app'],
        }
        apps = list(db.select('application', vars, where='name=$name'))
        if len(apps) == 0:
            return json.dumps(r)
        app = apps[0]

        vars = {
            'app_name'      : i['app'],
            'host'          : web.ctx.ip,
            'port'          : i['port'],
        }
        instances = list(db.select('instance', vars, where='app_name=$app_name and host=$host and port=$port'))
        if len(instances) == 0:
            instance = {
                'app_id'        : app.id,
                'app_name'      : app.name,
                'host'          : web.ctx.ip,
                'port'          : i['port'],
                'status'        : 1,
                'last_ack'      : sql('now()'),
                'create_date'   : sql('now()'),
                'update_date'   : sql('now()'),
            }
            db.insert('instance', **instance)
        else:
            vars = {
                'id'    : instances[0].id
            }
            db.update('instance', vars=vars, where='id=$id', status=1, last_ack=sql('now()'), update_date=sql('now()'))
        r['success'] = True
        return json.dumps(r)

class api_instance_unregister:
    def GET(self):
        i = web.input()
        web.header('Content-Type', 'application/json')
        r = {
            'success':  False,
            'data':     None,
        }

        if not i['app'] or i['app'].strip() == '':
            return json.dumps(r)
        if not i['port'] or not i['port'].isdigit():
            return json.dumps(r)

        vars = {
            'app_name'      : i['app'],
            'host'          : web.ctx.ip,
            'port'          : i['port'],
        }
        instances = list(db.select('instance', vars, where='app_name=$app_name and host=$host and $port=$port'))
        if len(instances) >= 0:
            vars = {
                'id'    : instances[0].id
            }
            db.update('instance', vars=vars, where='id=$id', status=0, last_ack=sql('now()'), update_date=sql('now()'))
        r['success'] = True
        return json.dumps(r)

class api_instance_keepalive:
    def GET(self):
        i = web.input()
        web.header('Content-Type', 'application/json')
        r = {
            'success':  False,
            'data':     None,
        }

        if not i['app'] or i['app'].strip() == '':
            return json.dumps(r)
        if not i['port'] or not i['port'].isdigit():
            return json.dumps(r)

        vars = {
            'app_name'      : i['app'],
            'host'          : web.ctx.ip,
            'port'          : i['port'],
        }
        instances = list(db.select('instance', vars, where='app_name=$app_name and host=$host and port=$port'))
        if len(instances) >= 0:
            vars = {
                'id'    : instances[0].id
            }
            db.update('instance', vars=vars, where='id=$id', status=1, last_ack=sql('now()'), update_date=sql('now()'))
        r['success'] = True
        return json.dumps(r)

class api_item_list:
    def GET(self):
        r = {
            'success':  True,
            'data':     {
                'items' : [],
            },
        }
        web.header('Content-Type', 'application/json')

        app_name = web.input(app='')['app']
        vars = {
            'app_name'    : app_name,
        }
        apps = list(db.select('application', vars, where='name = $app_name'))
        app = apps[0] if len(apps) > 0 else None
        if not app:
            return json.dumps(r)
        vars = {
            'app_id'    : app.id,
        }
        items = list(db.select('item', vars, where='app_id = $app_id'))
        r['data']['items'] = items
        return json.dumps(r, cls=JsonEncoderX)

def auth_processor(handler):
    if web.ctx.path in ['/login', '/register.json', '/unregister.json', '/keepalive.json', '/listItems.json']:
        return handler()
    # auth
    if not session.get('authed'):
        web.seeother(sso_login_url)
    result = handler()
    return result

def log_processor(handler):
    print '[%s] [%s] [url=%s%s (%s)]' % (web.ctx.ip, session.get('name'), web.ctx.path, web.ctx.query, web.ctx.method)
    return handler()

web.config.debug = ESWITCH_DEBUG
sso_login_url = SSO_LOGIN_URL
sso_login = SSO_LOGIN
db = web.database(dbn='mysql', host=DATABASE_HOST, port=DATABASE_PORT, user=DATABASE_USER, pw=DATABASE_PASSWORD, db=DATABASE_DB)
render = render_jinja(
    'templates',
    encoding = 'utf-8',
)
app = web.application(urls, globals())
session = web.session.Session(app, web.session.DiskStore('sessions'))
app.add_processor(auth_processor)
app.add_processor(log_processor)

if __name__ == "__main__":
    app.run()
