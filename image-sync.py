import sys
import time
import logging
import requests
import json
from datetime import datetime
from datetime import date
import time
from threading import Timer
from threading import Thread
import threading

from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler


from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


green_text = "\033[1;32;40m"
white_text = "\033[1;37;40m"
yellow_text = "\033[1;33;40m"

# load config file
f = open('./configuration.json')
config = json.load(f)
upload_threshold = config['threshold']['upload']
training_threshold = config['threshold']['train']
action = config['dataset']['action']
url = config['credentials']['endpoint']
dataset_name = config['dataset']['name']
action = config['dataset']['action']

# TODO, add action logic


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
        # headers = {
        #     'X-Auth-Token': token
        # }
        return token
    else:
        print(f"failure getting token HTTP {r.status_code}")


# TODO deliver minor feedback, UI prevents duplicate category names, but API does not
def create_dataset(name):
    # headers = {
    #     'X-Auth-Token': token
    # }
    body = {
        "name": name
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
    # print(headers)
    r = requests.get(f"{url}api/datasets", headers=headers, verify=False)
    if r.status_code == 200:
        datasets = r.json()
        global ds_ids
        ds_ids = {}
        for d in datasets:
            # print(d)
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
    # headers = {
    #     'X-Auth-Token': token
    # }
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

def get_dataset_files(dataset_id):
    # dataset_id = ds_ids[dataset_name]['_id']
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
        # ds_ids[dataset_name]['categories'] = d
        return d

# TODO, add logic to skip files that already exist
# TODO, add case if images don't have category? Or are not in folder
files_to_upload = {}
def upload_files(): # dataset_name):
    global files_to_upload
    print(f"uploading {sum([len(files_to_upload[f]) for f in files_to_upload.keys()])} files")
    print(f"filenames {files_to_upload}")
    dataset_name = config['dataset']['name']
    for category in files_to_upload.keys():
        print(f'uploading "{category}" images')
        dataset_id = ds_ids[dataset_name]['_id']
        # categories = ds_ids[dataset_name]['categories']
        # print(f"info for dataset {dataset_name}")
        print(ds_ids[dataset_name]['categories'])
        # for name in ds_ids:
        #     print(name)
        #     print(ds_ids[name]['categories'])

        if (category not in ds_ids[dataset_name]['categories'].keys()):
            print(f"category {category} does not exist in dataset {dataset_name}, creating")
            #TODO
            c = create_dataset_category(dataset_name, category)
            ds_ids[dataset_name]['categories'].update(c)
            # categories = ds_ids[dataset_name]['categories']
        else:
            print(f"category {category} already exists in dataset {dataset_name}")
        categories = ds_ids[dataset_name]['categories']
        # print(f'categories {categories}')
        # print(f'category {category}')
        files = [ ('files', open(file, 'rb') ) for file in files_to_upload[category]]
        files.append( ("category_name", category))
        files.append( ("category_id", categories[category]))
        # print(files)
        r = requests.post(f"{url}api/datasets/{dataset_id}/files", headers=headers, files=files, verify=False)
        # print(r)
        if r.status_code == 200:
            print(f"{len(files) - 2} {category} files posted to dataset {dataset_id}")
            global file_upload_count
            file_upload_count = 0
        else:
            print(f"error uploading file(s), HTTP {r.status_code}")
    files_to_upload = {}
        # TODO zip if more than 5 files


def train_model(dataset_id, action): #action=None, strategy={}):
    print("training model")
    t = date.fromtimestamp(time.time()).strftime("%m%d%Y-%H%M%S")
    # ds_id = ds_ids[name]['id']
    # dataset_id
    # name = config['model']['name']
    if action == "retrain":
        name = config['model']['name']
    elif action == "train":
        # TODO may cause clutter creating a new model every x files. Perhaps we can only keep most recent 5 models or so, remove oldest
        name = config['model']['name'] + t
    elif action == "nothing":
        return
    body = {
        "action": "create", # hardcoding to classifier for now. TODO, can add object detection if object coords are included in a json file
        "dataset_id": dataset_id,
        # pretrained_model: "", # TODO use in case of retrain?
        # strategy: strategy,
        "name": name
    }
    r = requests.post(f"{url}api/dltasks", headers=headers, json=body, verify=False)
    if r.status_code == 200:
        print(f"training model for dataset {dataset_name}")
        global file_train_count
        file_train_count = 0
    else:
        print(f"error training model, {r.status_code}")
        print(f"{r.text}")


# On start

# get PAIV token
token = get_token(config)
headers = {
    'X-Auth-Token': token
}

# get dataset information (categories, files)
ds_ids = get_datasets()
dataset_name = config['dataset']['name']
if dataset_name not in ds_ids.keys():
    ds_ids[dataset_name] = create_dataset(dataset_name)


# TODO, should only get info for dataset in the config file
# for name in ds_ids:
    # ds_id = ds_ids[name]['_id']
    # ds_ids[name]['categories'] = get_dataset_categories(ds_id)
    # ds_ids[name]['files'] = get_dataset_files(ds_id)

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
    ],
    "glacier": [
        "file3.png",
        "file4.png"
    ]
}

files_to_upload.keys()
'''

ds_id = ds_ids[dataset_name]['_id']
ds_ids[dataset_name]['categories'] = get_dataset_categories(ds_id)
ds_ids[dataset_name]['files'] = get_dataset_files(ds_id)

# ds_ids = get_dataset_info() # should refresh info every x hours



# Monitor folder, trigger file upload after x number of files gets added
# global file_count
# file_count = 0

file_upload_count = 0
file_train_count = 0

global upload_timer
global train_timer

def start_upload_timer():
    # We're using an timer in case the user adds more files to any of the subfolders after the threshold is met
    # This will give the user a buffer of x seconds to add more files. Timer is reset every time the
    upload_thread = list(filter(lambda t: (t.name == 'upload_timer'), threading.enumerate()))
    if upload_thread: #'upload_timer' in [t.name == 'upload_timer' for t in threading.enumerate()]:
        print("more files added, resetting upload timer")
        upload_thread[0].cancel()
    else:
        print("files exceed threshold, starting upload timer")
    upload_timer_wait_time = 5.0
    print(f"waiting for {upload_timer_wait_time} seconds to upload files")
    upload_timer = Timer(upload_timer_wait_time, upload_files) #, args=[files_to_upload], name="upload_timer")
    upload_timer.name = 'upload_timer'
    upload_timer.start()


def reset_upload_timer():
    # reset upload timer and append additional images IF images match same category
    print("more files added, resetting upload timer")
    upload_timer.cancel()
    # upload_timer.args()
    # args = args + upload_timer.args()
    # upload_files(files_to_upload, config['dataset']['name'])
    upload_timer = Timer(10.0, upload_files, name="upload_timer") #, args=[files_to_upload], name="upload_timer")
    upload_timer.start()

def wait_for_uploads(train_timer):
    for i in range(0,3):
        upload_thread = filter(lambda t: (t.name == 'upload_timer'), threading.enumerate())
        if upload_thread: #threading.active_count() > 1:
            print("waiting for uploads to complete")
            time.sleep(10)
        else:
            break
    train_timer.start()

def start_training_timer():
    train_thread = list(filter(lambda t: (t.name == 'train_timer'), threading.enumerate()))
    if train_thread:
        print("resetting training timer")
        train_thread[0].cancel()
    else:
        print("starting training timer")
        # print("files exceed threshold, starting upload timer")
    # t = Timer(10.0, train_model( ds_ids[dataset_name]['_id'], config['model']['action']))
    train_timer = Timer(10.0, train_model, args=[ds_ids[dataset_name]['_id'], config['model']['action']])
    train_timer.name = "train_timer"
    # check if upload thread is running, if so wait for 30 seconds
    # for i in range(0,3):
    #     upload_thread = filter(lambda t: (t.name == 'upload_timer'), threading.enumerate())
    #     if upload_thread: #threading.active_count() > 1:
    #         print("waiting for uploads to complete")
    #         time.sleep(10)
    #     else:
    #         break
    # train_timer.start()
    wait_uploads_thread = Thread(target = wait_for_uploads, args = [train_timer])
    wait_uploads_thread.start()


def reset_training_timer():
    train_timer.cancel()
    # check if upload thread is running, if so wait for 25 seconds
    for i in range(0,5):
        upload_thread = filter(lambda t: (t.name == 'upload_timer'), threading.enumerate())
        if upload_thread: #threading.active_count() > 1:
            print("waiting for uploads to complete")
            time.sleep(5)
    train_timer = Timer(5.0, train_model, args=[ds_ids[dataset_name]['_id'], config['model']['action']])
    train_timer.name = "train_timer"
    train_timer.start()

'''
Files are added to subfolder

Determine if the number of files exceed the 'upload' threshold

    If they do, we schedule a thread to upload the files

If additional files are added during the countdown, we'll cancel and reschedule a new upload thread

We'll then see if the files exceed the 'train' threshold

If so, we'll create a training thread

We'll wait until all other upload threads are finished before starting the training thread

'''

total_file_count = 0
class Event(LoggingEventHandler):
    # file_upload_count = 0
    # file_train_count = 0
    def on_created(self, event):
        global total_file_count
        global file_upload_count
        global file_train_count
        print(">>>>>>>>>> new file added <<<<<<<<<<<<")
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
        total_file_count += 1
        file_upload_count += 1
        file_train_count += 1
        print(f'upload: {file_upload_count} / {upload_threshold}')
        print(f'training: {file_train_count} / {training_threshold}')
        print(f'total_file_count: {total_file_count}')
        if file_upload_count >= upload_threshold:
            print(yellow_text)
            print(white_text)
            start_upload_timer()
            # if 'upload_timer' in [t.name for t in threading.enumerate()]:
                # reset_upload_timer()
            # if action == "append":
            # if ('upload_timer' in vars() or 'upload_timer' in globals()) and (upload_timer.is_alive()):
            # if threading.active_count() > 1:
                # reset_upload_timer()
            # else:
                # start_upload_timer()
            # upload_files(files_to_upload, config['dataset']['name'])
            # print("resetting file_upload_count")

        if file_train_count >= training_threshold:
            print(green_text)
            print(f"{file_train_count} files added to folders, training model")
            print(white_text)
            # upload_files(files_to_upload)
            # TODO, think through, should wait x seconds after training threshold is passed in case user is still adding additional files
            # We'll have a delay here in case more images are in the process of being copied or uploaded
            training_delay = 10 # have a delay of 10 seconds before training
            start_training_timer()
            # if ('train_timer' in vars() or 'train_timer' in globals()) and (train_timer.is_alive()):
            # # if threading.active_count() > 1:
            #     reset_training_timer()
            # else:
            #     start_training_timer()
            #     # getting multiple

            print(f"training model in {training_delay} seconds")
            # file_train_count = 0

            '''
            # wait until other upload threads are complete
            threading.active_count()
            '''
            # time.sleep(training_delay)
            # print("starting timer")
            # start_timer()
            # train_model( ds_ids[dataset_name]['_id'], config['model']['action'])
            # print("resetting file_train_count")
            print(white_text)

            # time.sleep(3)
        print("finished handling added file")

        # files.append(event.src_path)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    # path = config['folders']
    event_handler = Event()
    observer = Observer()
    if config['folders']:
        for folder in config['folders']:
            observer.schedule(event_handler, folder, recursive=True)
    else:
        path = sys.argv[1] if len(sys.argv) > 1 else '.'
        observer.schedule(event_handler, path, recursive=True)
    observer.start()
    print(f"Observing files in {config['folders']}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
