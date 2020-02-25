import sys
import time
import logging
import requests
import json
from datetime import datetime

from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler


from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


# load config file
f = open('./configuration.json')
config = json.load(f)
threshold = config['threshold']
action = config['dataset']['action']
url = config['credentials']['endpoint']
dataset_name = config['dataset']['name']

# TODO, add action logic
# "action" determines whether to append to existing dataset, or to create a new one. "append" or "create"
action = config['dataset']['action']


# Paiv calls

def get_token(config):
    credentials = config['credentials']
    body = {
        'grant_type':'password',
        'username': config['credentials']['username'],
        'password': config['credentials']['password']
    }
    url = config['credentials']['endpoint'] + 'api/tokens' # + config['credentials']['port']
    print(f'posting to {url}')
    headers = {'content-type': 'application/json'}
    r = requests.post(url, json=body, headers=headers, verify=False)
    if r.status_code == 200:
        res = r.json()
        global token
        token = res['token']
        print(f"setting token {token}")
        headers = {
            'X-Auth-Token': token
        }
    else:
        print(f"failure getting token HTTP {r.status_code}")


# TODO deliver minor feedback, UI prevents duplicate category names, but API does not
def create_dataset(name):
    # headers = {
    #     'X-Auth-Token': token
    # }
    body = {
        name: name
    }
    r = requests.post(f"{url}api/datasets", headers=headers, json=body, verify=False)
    if r.status_code == 200:
        print(f"dataset {name} created")
        res = r.json()
        ds = {
          "_id": res["dataset_id"],
          "name": name
        }
        return ds
        # global datasets
        # datasets.append(


# lambda

# item.get('id') == 2

def get_datasets():
    # global datasets
    # headers = {
    #     'X-Auth-Token': token
    # }
    r = requests.get(f"{url}api/datasets", headers=headers, verify=False)
    if r.status_code == 200:
        datasets = r.json()
        global ds_ids
        ds_ids = {}
        for d in datasets:
            print(d)
            ds_ids[d['name']] = {
                "_id": d['_id'],
                "categories": []
            }
            # get_dataset_categories(d['name'])
        # print(ds_ids)
        return ds_ids
    else:
        print(f"error getting datasets")
        print(r.status_code)

def get_dataset_categories(dataset_id):
    headers = {
        'X-Auth-Token': token
    }
    # dataset_id = ds_ids[dataset_name]['_id']
    r = requests.get(f"{url}api/datasets/{dataset_id}/categories", headers=headers, verify=False)
    if r.status_code == 200:
        # global ds_categories
        # global ds_ids
        ds_categories = r.json()
        categories = {}
        for c in ds_categories:
            categories[c['name']] = c['_id']

        ds_ids[dataset_name]['categories'] = categories
        print(f"dataset {dataset_id} categories received {categories}")
        return categories
    else:
        print(f"error getting dataset categories {r.status_code}")


def get_dataset_files(dataset_name):
    dataset_id = ds_ids[dataset_name]['_id']
    r = requests.get(f"{url}api/datasets/{dataset_id}/files", headers=headers, verify=False)
    if r.status_code == 200:
        dataset_files = r.json()
        return dataset_files
    else:
        print("error retreiving dataset files")
        return []


def create_dataset_category(dataset_name, category_name):
    body = {
      "name": category_name
    }
    dataset_id = ds_ids[dataset_name]['_id']
    r = requests.post(f"{url}api/datasets/{dataset_id}/categories", headers=headers, json=body, verify=False)
    if r.status_code == 200:
        print(f"added dataset category {category_name}")
        category_id = r.json()['dataset_category_id']
        d = {
            category_name: category_id
        }
        ds_ids[dataset_name]['categories'] = d
        return d




'''
# examples

ds_ids = {
    "dataset1": {
        id: "4n231ji-12412n",
        categories: ["car", "plant"]
    }
}

files_to_upload = {
    "car": [
        "file1.png",
        "file2.png"
    ]
}
'''





# TODO, add logic to skip files that already exist
def upload_files(files_to_upload, dataset_name):
    print(f"uploading {len(files_to_upload.keys())} files")
    # TODO, add case if images don't have category? Or are not in folder
    # dataset_name = config['dataset']['name']
    for category in files_to_upload.keys():
        print(f'uploading "{category}" images')
        dataset_id = ds_ids[dataset_name]['_id']
        categories = ds_ids[dataset_name]['categories']
        if (category not in categories.keys()):
            print(f"category {category} does not exist in dataset {dataset_name}, creating")
            create_dataset_category(dataset_name, category)
            categories = ds_ids[dataset_name]['categories']
        else:
            print(f"category {category} already exists in dataset {dataset_name}")
        files = [ ('files', open(file, 'rb') ) for file in files_to_upload[category]]
        files.append( ("category_name", category))
        files.append( ("category_id", categories[category]))
        print(files)
        # data = {"category_name": category}
        print(f"posting to {url}api/datasets/{dataset_id}/files")
        r = requests.post(f"{url}api/datasets/{dataset_id}/files", headers=headers, files=files, verify=False)
        print(r)
        if r.status_code == 200:
            print(f"{len(files) - 2} {category} files posted to dataset {dataset_id}")
        else:
            print(f"error uploading file(s), HTTP {r.status_code}")
    files_to_upload = {}
        # TODO zip if more than 5 files

def train_model(dataset_id, dataset_name): #action=None, strategy={}):
    # t = date.fromtimestamp(time.time()).strftime("%m_%d_%Y_%H%M%S")
    # ds_id = ds_ids[name]['id']
    # dataset_id
    # name = config['dataset']['name']
    body = {
        action: "create", # hardcoding to classifier for now. TODO, can add object detection if object coords are included in a json file
        dataset_id: dataset_id,
        # strategy: strategy,
        name: dataset_id + t
    }
    r = requests.post(f"{url}api/dltasks", headers=headers, json=body, verify=False)
    if r.status_code == 200:
        print(f"began training model for {}")

if 'token' not in config['credentials'].keys():
    get_token(config)
    config['token'] = token
    # config['time_token_received'] =
    headers = {
        'X-Auth-Token': token
    }
else:
    print(f"token already in config file: {config['credentials']['token']}")
    token = config['credentials']['token']
    headers = {
        'X-Auth-Token': token
    }

# get_datasets()


# get dataset information (categories, files)
ds_ids = get_datasets()

dataset_name = config['dataset']['name']
if dataset_name not in ds_ids.keys():
    ds_ids[dataset_name] = create_dataset(dataset_name)

for name in ds_ids:
    ds_id = ds_ids[name]['id']
    ds_ids[name]['categories'] = get_dataset_categories(ds_id)
    ds_ids[name]['files'] = get_dataset_files(ds_id)

# return ds_ids


# Monitor folder, trigger file upload after x number of files gets added
# global file_count
# file_count = 0
files_to_upload = {}
global file_upload_count
global file_train_count
file_upload_count = 0
file_train_count = 0
class Event(LoggingEventHandler):
    def on_created(self, event):
        print("file added to folder")
        print(event.src_path)
        split_path = event.src_path.split('/')
        filename = split_path[-1]
        category = split_path[-2]
        if category not in files_to_upload.keys():
            files_to_upload[category] = []
        image_type = filename.split('.')[-1]
        if image_type not in ['jpg', 'png', 'mp4']:
            print(f"unsupported media type {image_type}")
            return
        files_to_upload[category].append(event.src_path)
        file_upload_count += 1
        file_train_count += 1
        print(f'{file_count} / {threshold}')
        if file_upload_count >= upload_threshold:
            print(f"uploading {file_upload_count} files")
            # if action == "append":
            upload_files(files_to_upload, config['dataset']['name'])
            file_upload_count = 0
        if file_train_count >= training_threshold:
            print(f"{file_train_count} files")
            # upload_files(files_to_upload)
            train_model( ds_ids[dataset_name]['id'] )
            file_train_count = 0

        # files.append(event.src_path)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    # path = config['folders']
    event_handler = Event()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
