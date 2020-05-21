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
import zipfile
import os

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
dataset_name = config['dataset']['name']

if 'action' in config['model'].keys():
    action = config['model']['action'].lower()
else:
    action = None

url = config['credentials']['endpoint']


# Paiv calls
def get_token(config):
    credentials = config['credentials']
    body = {
        'grant_type':'password',
        'username': config['credentials']['username'],
        'password': config['credentials']['password']
    }
    url = config['credentials']['endpoint'] + '/api/tokens' # + config['credentials']['port']
    print(f'posting to {url}/api/tokens')
    headers = {'content-type': 'application/json'}
    r = requests.post(url, json=body, headers=headers, verify=False)
    if r.status_code == 200:
        res = r.json()
        global token
        token = res['token']
        print(f"setting token {token}")
        return token
    else:
        print(f"failure getting token HTTP {r.status_code}")


def create_dataset(name):
    body = {
        "name": name
    }
    r = requests.post(f"{url}/api/datasets", headers=headers, json=body, verify=False)
    if r.status_code == 200:
        print(f"dataset {name} created")
        res = r.json()
        ds = {
          "_id": res["dataset_id"],
          "name": name
        }
        return ds


def get_datasets():
    r = requests.get(f"{url}/api/datasets", headers=headers, verify=False)
    if r.status_code == 200:
        datasets = r.json()
        global ds_ids
        ds_ids = {}
        for d in datasets:
            ds_ids[d['name']] = {
                "_id": d['_id'],
                "categories": []
            }
        return ds_ids
    else:
        print(f"error getting datasets")
        print(r.status_code)


def get_models():
    r = requests.get(f"{url}/api/trained-models", headers=headers, verify=False)
    if r.status_code == 200:
        models = r.json()
        return models
    else:
        print(f"error getting models")
        print(r.status_code)

def get_dataset_categories(dataset_id):
    r = requests.get(f"{url}/api/datasets/{dataset_id}/categories", headers=headers, verify=False)
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
    r = requests.get(f"{url}/api/datasets/{dataset_id}/files", headers=headers, verify=False)
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
    r = requests.post(f"{url}/api/datasets/{dataset_id}/categories", headers=headers, json=body, verify=False)
    if r.status_code == 200:
        print(f"added dataset category {category_name}")
        category_id = r.json()['dataset_category_id']
        d = {
            category_name: category_id
        }
        return d

# TODO, add logic to skip files that already exist
files_to_upload = {}
def upload_files():
    global files_to_upload
    global file_upload_count
    print(f"uploading {sum([len(files_to_upload[f]) for f in files_to_upload.keys()])} files")
    # print(f"filenames {files_to_upload}")
    dataset_name = config['dataset']['name']
    categories = ds_ids[dataset_name]['categories']
    for category in files_to_upload.keys():
        print(f'uploading "{category}" images')
        dataset_id = ds_ids[dataset_name]['_id']
        if (category not in ds_ids[dataset_name]['categories'].keys()):
            print(f"category {category} does not exist in dataset {dataset_name}, creating")
            c = create_dataset_category(dataset_name, category)
            ds_ids[dataset_name]['categories'].update(c)
        else:
            print(f"category {category} already exists in dataset {dataset_name}")
        num_files = len(files_to_upload[category])
        if num_files > 100:
            z = zipfile.ZipFile('images.zip', 'w')
            file_upload_count += num_files
            for file in files_to_upload[category]:
                z.write(file)
            files = [ ('files', open('images.zip', 'rb')) ]
        else:
            files = [ ('files', open(file, 'rb') ) for file in files_to_upload[category]]
        files.append( ("category_name", category))
        files.append( ("category_id", categories[category]))
        r = requests.post(f"{url}/api/datasets/{dataset_id}/files", headers=headers, files=files, verify=False)
        close_files = lambda f: f[1].close()
        map(close_files, files)
        if r.status_code == 200:
            print(f"{len(files) - 2} {category} files posted to dataset {dataset_id}")
        else:
            print(f"error uploading file(s), HTTP {r.status_code}")
    print("resetting file_upload_count")
    file_upload_count = 0
    files_to_upload = {}
    upload_in_progress = False

def train_model(dataset_id, action): #, strategy={}):
    global last_model_id
    global file_train_count
    t = date.fromtimestamp(time.time()).strftime("%m%d%Y-%H%M%S")
    body = {
        "action": action, #"create", # hardcoding to classifier for now. TODO, can add object detection if object coords are included in a json file
        "dataset_id": dataset_id,
    }
    if 'strategy' in config.keys():
        strategy = config['strategy']
    else:
        strategy = {}
    if action == "retrain":
        name = config['model']['name'] + t
        body['name'] = name
        if last_model_id:
            body['pretrained_model'] = last_model_id
    elif action == "train":
        # TODO may cause clutter creating a new model every x files. Perhaps we can only keep most recent 5 models or so, remove oldest
        name = config['model']['name'] + t
        body['name'] = name
    elif (action == None) or (action == "none"):
        return
    r = requests.post(f"{url}/api/dltasks", headers=headers, json=body, verify=False)
    if r.status_code == 200:
        last_model_id = r.json()['task_id']
        print(f"training model: {last_model_id} for dataset: {dataset_name}")
    else:
        print(f"error training model, {r.status_code}")
        print(f"{r.text}")
    print("resetting file_train_count")
    file_train_count = 0



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

last_model_id = None


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

# TODO, make timer global. if it's defined and counting down, restart
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
    upload_timer = Timer(10.0, upload_files, name="upload_timer") #, args=[files_to_upload], name="upload_timer")
    upload_timer.start()

def wait_for_uploads(train_timer):
    for i in range(0,3):
        upload_thread = list(filter(lambda t: (t.name == 'upload_timer'), threading.enumerate()))
        if upload_thread and upload_thread[0].isAlive(): #threading.active_count() > 1:
            print("waiting for uploads to complete")
            time.sleep(5)
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

def upload_existing_files():
    # upload files that are in folder and do not exist in dataset
    global files_to_upload
    global file_upload_count
    global file_train_count
    file_names = [f['original_file_name'] for f in ds_ids[dataset_name]['files']]
    for category in os.listdir(config['folders'][0]):
        if category not in files_to_upload.keys():
            files_to_upload[category] = []
        print(f"{config['folders'][0]}/{category}")
        for image in os.listdir( f"{config['folders'][0]}/{category}" ):
            if image in file_names:
                print(f"image {image} already exists in dataset, skipping")
                continue
            else:
                if len(files_to_upload[category]) < 10:
                    print(f"adding {image}")
                    files_to_upload[category].append(f"{config['folders'][0]}/{category}/{image}")
        file_upload_count += len(files_to_upload[category])
        file_train_count += len(files_to_upload[category])
        print(f"uploading {len(files_to_upload[category])} {category} images ")
    print(f" uploading {file_upload_count} total images")

    if file_upload_count > upload_threshold:
        print(yellow_text)
        print(white_text)
        # upload_in_progress = True
        start_upload_timer()
    if file_train_count > training_threshold:
        print(green_text)
        print(f"{file_train_count} files added to folders, starting model training timer")
        print(white_text)
        training_delay = 10 # have a delay of 10 seconds before training
        start_training_timer()

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
file_upload_count = 0
file_train_count = 0
upload_existing_files()

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
        if file_upload_count == upload_threshold:
            print(yellow_text)
            print(white_text)
            # upload_in_progress = True
            start_upload_timer()

        if file_train_count == training_threshold:
            print(green_text)
            print(f"{file_train_count} files added to folders, starting model training timer")
            print(white_text)
            training_delay = 10 # have a delay of 10 seconds before training
            start_training_timer()

            '''
            # wait until other upload threads are complete
            threading.active_count()
            '''
            print(white_text)
        print(f">>>>>> finished handling file {event.src_path} <<<<<<<")
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
