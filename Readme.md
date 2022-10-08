
# T&P Telegram Data analyzer 

### Intro 

This project works simply by dumping all the telegram messages form the Tnp group ( Telethon MTProto user api) and 
then using elastic search to find when was the first occurrence of the company name in the group

### System Requirement 

* Docker Desktop (which includes docker compose)
* Python 3.10


### Setting up Elastic 

The following command will start kibana and elastic in a docker container.

```shell
 docker compose up
```
This sets up kibana too. You can access the dashboard and visualise the data at [localhost:5601](http://localhost:5601)


### Setting up Telethon 

1. [Login to your Telegram account](https://my.telegram.org/) with the phone number of the developer account to use.
2. Click under API Development tools.
3. A Create new application window will appear. Fill in your application details. There is no need to enter any URL, and only the first two fields (App title and Short name) can currently be changed later.
4. Click on Create application at the end. Remember that your API hash is secret and Telegram won’t let you revoke it. Don’t post it anywhere!
5. Create a .env using the sample.env file and add the _TELEGRAM_API_ID_ and _TELEGRAM_API_HASH_


### Running the app

1. Installing the requirements
 ```shell
pip3 install -r requirements.txt
```
2. Start the main program
```shell
python main.py
```
3. Use you telegram phone number(starting with +91)
```shell
Please enter your phone (or bot token): +919700000000
```
4. Get the login code form any telegram client on web or phone
5. If you have not configured the tnp chat Id in the env file. The app will dump all the ids of each chat your account is in, find out the chat id, corresponding 
to the tnp group. Once u have the chat ID add it to the env file,and it won't prompt for following sessions.
6. The rest of the process is automated.
7. The telegram message dump line can be commented out, once it's done for the first time
```python
async def main():
    global tnp_id
    load_companies()
    if tnp_id == -1:
        await dump_telegram_ids()
        tnp_id = int(input("Check the Dump above and enter the tnp chat id : "))
    # await dump_telegram_messages()
    search_elastic()
```

