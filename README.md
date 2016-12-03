# quinielas-uc3m
A python daemon to automate quinielas in the telematics department of UC3M (work in progress)

## Steps to launch daemon
Right after clonning the repo, you have to create `config.json` and `people.txt` files based on the `*_base*` files.

`config_base.json`:
```json
{
    "secretFile": "client_secret.json",
    "credentials": ".credentials",
    "spreadSheetId": "___SPREADSHEET_ID___",
    "plantillaId": ___id_of_plantilla___ (number),
    "appName": "___APP_NAME___",
    "people": "people.txt",
    "numDoubles": ___num_of_doubles___ (number),
    
    "periodNew": ___seconds_interval_check_new___ (number),
    "periodCompleted": ___seconds_interval_check_completed___ (number),
    "periodFinished": ___seconds_interval_check_finished___ (number)

}
```
where the `period*` parameters specify the number of seconds to spend in each state bedore checking for a new event. You should store your Google's API secret file in `client_secret.json`, and the credentials will be stored under the `.credentials` folder.


`people.txt`:
```txt
name1
name2
...
```
Store in each line the name of the person participating. This file can be modified during the daemon's execution. The change implies that in the next event involving the people, the daemon will read the file again and take changes into account.

---

## How does it work?
The daemon is basically a state machine with following states:
 1. NEW
 2. COMPLETED
 3. FINISHED

The daemon waits for events to change for one state to another:
 1. NEW->COMPLETED when all the people has filled their columns.
 2. COMPLETED->FINISHED when all football matches have finished.
 3. FINISHED->NEW when a new sheet is created. This is accomplished by **creating a sheet having as title the number of next quiniela**. For example, if quiniela number 22 according to Loterías y Apuestas del Estado, you'll have to create a sheet entitled '22'.
 
 *Note*: take into account that after the creation of the new sheet, you'll have to wait a maximum of `periodFinished` seconds before the daemon renames it, and fills it with the football matches.
 
 *Note*: make sure that before you create a new sheet, the matches are scheduled available at [http://resultados.as.com/quiniela/2016_2017/jornada_y](http://resultados.as.com/quiniela/2016_2017/), where `y` is the number of next quiniela day. Otherwise the daemon can crash.

## Daemonize
To daemonize the script you can run the following line:
```bash
nohup ./daemon.py > log.txt 2>&1 &
```
with this line, if script dies or the machine turns off, it won't start by itself.

