# Upload PowerAI Vision datasets

In this code pattern, we show how to simplify the model training process in PowerAI Vision.

Business users using PowerAI Vision's image classification process will need to manually upload and categorize images, which can become rather tedious when working with large datasets.

Here we're providing a long-running script that'll enable the user to automate the training process for image classification models. They can upload and categorize images by simply adding images to a folder.

This script works by monitoring a folder containing one or more subfolders. Each subfolder contains images, and the subfolder name should match the category of the image sets.

<!-- Architecture -->
<img src="https://i.imgur.com/Fg9j0MS.png">

#  Components

* [PowerAI Vision](https://www.ibm.com/products/maximo). This is an image analysis platform that allows you to build and manage computer vision models, upload and annotate images, and deploy apis to analyze images and videos.

Sign up for a trial account of PowerAI vision [here](https://developer.ibm.com/linuxonpower/deep-learning-powerai/try-powerai/). This link includes options to provision a PowerAI Vision instance either locally on in the cloud.

# Flow

1. User copies respective images to category subfolders.
2. Script counts number of images added, determines if image count exceeds threshold.
3. If image count exceeds "upload" threshold, script executes a POST request uploading images for each category.
4. If image count exceeds "train" threshold, script executes a POST request to begin training a model.


# Prerequisites

* An account on IBM Marketplace that has access to PowerAI Vision. This service can be provisioned [here](https://developer.ibm.com/linuxonpower/deep-learning-powerai/vision/access-registration-form/)

* Python 3


# Steps

Follow these steps to setup and run this Code Pattern.
1. [Clone repository](#1-clone-repository)
2. [Create image folder and subfolders](#2-create-image-folder-and-subfolders)
3. [Fill in configuration file](#3-fill-in-configuration-file)
4. [Start and test script](#4-start-and-test-script)
<!-- 5. [Register script as a service](#5-register-script-as-a-service) -->


## 1. Clone repository

```
git clone https://github.com/ibm/powerai-data-sync
```

## 2. Create image folder and subfolders

```
mkdir images

# run following command for each category in your classifier
mkdir images/<category_name>
```


## 3. Fill in configuration file

Copy configuration file from template.

```
cp configuration.json.template configuration.json
```

Open configuration file and fill in PowerAI Vision credentials in the "credentials" object.

```
"credentials": {
  "endpoint": "<url>",
  "username": "<username>",
  "password": "<password>",
}
```


Next we'll configure the classification model to be trained once enough files have been uploaded. Give the model a name, and specify an action to take. Valid actions can be to "train" a new model, "retrain" an existing model, or "nothing" if you'd rather not train a model at all. Also, the "strategy" parameter can be provided to further customize the training process, such as how many iterations, type of neural network to train, and so on. The custom training parameters can be found in the api documentation [here](https://public.dhe.ibm.com/systems/power/docs/powerai/powerai-vision-api.html#dltasks_post)

```
"model": {
  "name": "<name_of_model>",
  "action": "train",
  "strategy": {}
},
```

Specify the full path to the folder(s) that will be monitored by the script
```
"folders": [
  "<path to root image folder>",
]
```

## 4. Start and test script

Start the script with the following command

```
python3 image-sync.py
```

If the script is able to successfully authenticate,

<img src="https://i.imgur.com/WNHQI8x.png" />


Next, copy a few images into the various category folders. The logs will show which files were added, and how  many more images are needed to meet the threshold.

<img src="https://i.imgur.com/2v2bTHb.png" />

<!-- ## 5. Register script as a service

Mac OSX
```
```

*Linux*
Open the systemd [service file](service-files/paiv-sync.service#L3)
Enter the path to your script in the "Service" section like so
`Environment=SCRIPT_PATH=<script path>`

Copy and enable systemd file
```
cp service-files/paiv-sync.service /lib/systemd/system/
systemctl enable paiv-sync
systemctl start paiv-sync
```

Confirm service is running
```
systemctl status paiv-sync
``` -->


<!-- # Create a root folder

# Create subfolders. Script assumes subfolder will match category name.

#

The script will monitor a folder that has one or more subfolders. Each subfolder contains images, and the subfolder name should match the category of the image sets.



```
{
  "credentials": {
    "endpoint": "<url>",
    "port": "8000",
    "username": "<username>",
    "password": "<password>",
  },
  "recursive": 1,
  "threshold": {
    "training": 3,
    "upload": 3
  },
  "skip_duplicates": 1,
  "time": 10,
  "dataset": {
    "name": "classifier",
    "action": "append"
  },
  "model": {
    "name": "classifier",
    "action": "retrain"
    "_comment": "action can be retrain, train, or nothing. default to 'train'. TODO, remember that training a new model will of course result in anew ID",
    "strategy": {}
  },
  "folders": [
    "/Users/kkbankol@us.ibm.com/projects/powerai-data-sync/images"
  ],
  "categories": {
    "buildings": "buildings"
    "_comment": "this section is entirely optional, used to override category if user would prefer not to use subfolder"
  }
}
```

# TODO, implement suggestion from below to add python script as a background windows service
https://stackoverflow.com/a/32440



// dataset_action options can be to either append or create. \n
// if create, use name as prefix with timestamp, and train a new model.\n
// if appending to existing dataset, retrain model \n
",



"comment": "\n
// here, we're assuming that the category of a set of images match their enclosing folder name. \n
// if that is not the case, override the category name here (folder_name: category_name) \n




"comment": "// number of images that can be added until upload is triggered",


"comment": "// time (seconds) to wait after threshold is surpassed to upload", -->

# License

This code pattern is licensed under the Apache Software License, Version 2.  Separate third party code objects invoked within this code pattern are licensed by their respective providers pursuant to their own separate licenses. Contributions are subject to the [Developer Certificate of Origin, Version 1.1 (DCO)](https://developercertificate.org/) and the [Apache Software License, Version 2](https://www.apache.org/licenses/LICENSE-2.0.txt).

[Apache Software License (ASL) FAQ](https://www.apache.org/foundation/license-faq.html#WhatDoesItMEAN)
