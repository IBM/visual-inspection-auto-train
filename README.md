
# Create a root folder

# Create subfolders. Script assumes subfolder will match category name.

#


```
{
  "credentials": {
    "endpoint": "<powerai_vision_url>:<powerai_vision_port>",
    "username": "<username>",
    "password": "<password>",
    "time_token_received": "",
    "token": "35bf6b87-be86-427d-b95d-b45651b3f41e"
  },
  "recursive": 1,
  "threshold": 3,
  "skip_duplicates": 1,
  "time": 10,
  "dataset": {
    "name": "classifier",
    "action": "append"
  },
  "folders": [
    "/Users/kkbankol@us.ibm.com/projects/powerai-data-sync/images"
  ],
  "categories": {
    "buildings": "buildings"
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


"comment": "// time (seconds) to wait after threshold is surpassed to upload",
