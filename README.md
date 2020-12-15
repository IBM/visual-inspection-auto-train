# Upload IBM Maximo Visual Inspection datasets

In this code pattern, we show how to simplify the model training process in IBM Maximo Visual Inspection.

Currently, business users using the IBM Maximo Visual Inspection image classification process will need to manually upload and categorize images. These manual steps can become rather tedious when working with large datasets.

Here we're providing a long-running script that'll enable the user to automate the training process for image classification models. They can upload and categorize images by simply adding images to a folder.

This script works by monitoring a folder containing one or more subfolders. Each subfolder contains images, and the subfolder name should match the category of the image sets.

<!-- Architecture -->
<img src="https://developer.ibm.com/developer/default/patterns/derive-insights-from-asset-on-a-transmission-tower/images/architecture.png">

#  Components

* [IBM Maximo Visual Inspection](https://www.ibm.com/products/maximo). This is an image analysis platform that allows you to build and manage computer vision models, upload and annotate images, and deploy apis to analyze images and videos.

Sign up for a trial account of IBM Maximo Visual Inspection [here](https://developer.ibm.com/linuxonpower/deep-learning-powerai/try-powerai/). This link includes options to provision a IBM Maximo Visual Inspection instance either locally on in the cloud.

# Flow

1. User copies respective images to category subfolders.
2. Script counts number of images added, determines if image count exceeds threshold.
3. If image count exceeds "upload" threshold, script executes a POST request uploading images for each category.
4. If image count exceeds "train" threshold, script executes a POST request to begin training a model.


# Prerequisites

* An account on IBM Marketplace that has access to IBM Maximo Visual Inspection. This service can be provisioned [here](https://developer.ibm.com/linuxonpower/deep-learning-powerai/vision/access-registration-form/)

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

In this step, we'll create a folder and category subfolders.

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

Now we'll need to fill in data in a few required sections.

Open the `configuration.json` file and fill in IBM Maximo Visual Inspection credentials in the "credentials" object.

#### Credentials

```
"credentials": {
  "endpoint": "https://<maximo_visual_inspection_url>",  
  "username": "<maximo_visual_inspection_username>",
  "password": "<maximo_visual_inspection_password>",
}
```

#### Dataset

Next we can define our dataset. We'll simply provide a name here.

```
"dataset": {
  "name": "classifier"
}
```

#### Model

Next we'll configure the classification model which will be trained once enough files have been uploaded. Give the model a name, and specify an action to take. Valid actions can be to "train" a new model, "retrain" an existing model, or "none" if you'd rather not train a model at all.

The "train" option will create a new model with the provided name and an appended timestamp. If a previous model with the same name/dataset has been trained, we will use the newest version of that model as a starting point. This is the recommended option as it will result in the fastest training times.

The "retrain" option will create a new model with the provided name and an appended timestamp. This will begin training from the beginning, so this option will result in longer training times.

```
"model": {
  "name": "<name_of_model>",
  "action": "train",
  "strategy": {}
},
```

#### Threshold

Then, we'll define threshold parameters. The threshold should be an integer specifying how many images can be added to a folder before some action is taken. In this case, we have an "upload" threshold which will cause the process to begin uploading images to a dataset once that threshold has been passed. And we also have a "training" threshold will trigger a new model training process.

```
"threshold": {
  "upload": 3,
  "training": 10
},
```

#### Optional Model Parameters
We can further define the type of model that will be trained with optional parameters.

For example, we can add the `nn_arch` parameter to specify what kind of neural network will be trained. Valid options are "tiny_yolo_v2" (tiny YOLO v2), "frcnn" (FRCNN), and "frcnn_mrcnn" (Segmentation Training). If this parameter is not provided, the system will default to building a "FRCNN" model.

We can also specify a pretrained_model to be used as a base model. This parameter is automatically added if using the "retrain" action, but you can override the model id here if there's a particular model you'd like to use as a base.

The `strategy` object can be provided to further customize the training process, and define parameters as how many training iterations, a learning rate, etc.

For example, the following `model` object will generate a "Tiny YOLO V2" based model. This will use the specified `pretrained_model` as a base. And the `strategy` section defines the maximum iterations, number of test iterations, test interval, and a learning rate.
```
"model": {
  "name": "<name_of_model>",
  "action": "train",
  "pretrained_model": "<pretrained_model_id>
  "nn_arch": "tiny_yolo_v2"
  "strategy": {
      "max_iter": 1500,
      "test_iter": 100,
      "test_interval": 20,
      "learning_rate": 0.001
  }
},
```

A full list of the custom training parameters can be found in the api documentation [here](https://public.dhe.ibm.com/systems/power/docs/powerai/powerai-vision-api.html#dltasks_post)

#### Folder(s)
Finally, we'll need specify the full path to the folder(s) that will be monitored by the script. All subfolders within the provided folder will also be monitored.

```
"folders": [
  "<path to root image folder>",
]
```



A completed configuration file should look like so
```
{
  "credentials": {
    "endpoint": "<url>",
    "port": "8000",
    "username": "<username>",
    "password": "<password>",
  },
  "threshold": {
    "training": 3,
    "upload": 10
  },
  "skip_duplicates": 1,
  "time": 10,
  "dataset": {
    "name": "classifier",
  },
  "model": {
    "name": "classifier",
    "action": "retrain",
    "strategy": {}
  },
  "folders": [
    "<path to root image folder>",
    "<path to root image folder>"
  ],
  "categories": {
    "buildings": "buildings",
    "_comment": "this section is entirely optional, used to override category if user would prefer not to use subfolder"
  }
}

```



## 4. Start and test script

After setting up the configuration file, we can start the script with the following command.

```
python3 image-sync.py
```

This script will run indefinitely until the process is stopped. If the script is able to successfully authenticate, we'll see the following output in the console logs

<img src="https://i.imgur.com/WNHQI8x.png" />


Next, copy a few images into the various category folders. The logs will show which files were added, and how  many more images are needed to meet the threshold.

<img src="https://i.imgur.com/2v2bTHb.png" />

In the script output, we can see the total amount of images that have been added to the folder, and we can also compare that to the upload/training thresholds. The script output is updated every time files are added to the folder. In the bottom of the script output, we can see that our upload threshold has been surpassed, and that the images are to be uploaded to the dataset

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
    "_comment": "action can be retrain, train, or none. default to 'train'. TODO, remember that training a new model will of course result in anew ID",
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
