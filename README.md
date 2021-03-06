# Feature collector "tsp-fc"
***Version:*** 1.0

***Date:*** 15.04.2021

***Authors:***  [Ľuboš Buzna](https://github.com/lubos31262); [Milan Straka](https://github.com/bioticek)

***Address:*** University of Žilina, Univerzitná 8215/1, 010 26 Žilina, Slovakia
# Description 


The "tsp-fc" feature collector is  a module of the **Ride2Rail Offer Categorizer** responsible for the computation of the following determinant factors: ***"cleanliness"***, ***"space_available"***, ***"ride_smoothness"***, ***"seating_quality"***, ***"internet_availability"***, ***"plugs_or_charging_points"***, ***"silence_area_presence"***, ***"privacy_level"***, ***"user_feedback"*** , ***"bike_on_board"***, ***"likelihood_of_delays"*** , ***"last_minute_changes"***, ***"frequency_of_service"*** and ***"business_area_presence"***. 

Computation can be executed from ***["tsp.py"](https://github.com/Ride2Rail/tsp-fc/blob/main/code/tsp.py)*** by running the procedure ***extract()*** which is binded under the name ***compute*** with URL using ***[FLASK](https://flask.palletsprojects.com)*** (see example request below). Computation is composed of three phases:

***Phase I:***   Extraction of data required by tsp-fc feature collector from the cache. A dedicated procedure defined for
            this purpose from the unit ***"[cache_operations.py](https://github.com/Ride2Rail/r2r-offer-utils/wiki/cache_operations.py)"*** is utilized.

***Phase II:*** Computation of weights assigned to "tsp-fc" feature collector. For the aggregation of data at the tripleg level and for
            normalization of weights a dedicated procedure implemented in the unit ***"[normalization.py](https://github.com/Ride2Rail/r2r-offer-utils/wiki/normalization.py)"*** are utilized. By default "z-scores" are used to normalize data.


***Phase III:*** Storing of the results produced by "tsp-fc" to cache. A dedicated procedure defined for
            this purpose in the unit ***"[cache_operations.py](https://github.com/Ride2Rail/r2r-offer-utils/wiki/cache_operations.py)"*** is utilized.

# Configuration

The following values of parameters can be defined in the configuration file ***"tsp.conf"***.

Section ***"running"***:
- ***"verbose"*** - if value __"1"__ is used, then feature collector is run in the verbose mode,
- ***"scores"*** - if  value __"minmax_score"__ is used, the minmax approach is used for normalization of weights, otherwise, the __"z-score"__ approach is used. 

Section ***"cache"***: 
- ***"host"*** - host address where the cache service that should be accessed by ***"tsp-fc"*** feature collector is available
- ***"port"*** - port number where the cache service that should be accessed used by ***"tsp-fc"*** feature collector is available

**Example of the configuration file** ***"tsp.conf"***:
```bash
[service]
name = tsp
type = feature collector
developed_by = Lubos Buzna <lubos(dot)buzna(at)fri(dot)uniza(dot)sk> and Milan Straka<milan(dot)straka(at)fri(dot)uniza(dot)sk>

[running]
verbose = 1
scores  = z_scores

[cache]
host = cache
port = 6379
```

# Usage
### Local development (debug on)

The feature collector "tsp-fc" can be launched from the terminal locally by running the script "tsp.py":

```bash
$ python3 tsp.py
 * Serving Flask app "price" (lazy loading)
 * Environment: development
 * Debug mode: on
```
Moreover, the repository contains also configuration files required to launch the feature collector in Docker from the terminal by the command docker-compose up:


```bash
docker-compose up
Starting tsp_fc ... done
Attaching to tsp_fc
tsp_fc    |  * Serving Flask app "tsp.py" (lazy loading)
tsp_fc    |  * Environment: development
tsp_fc    |  * Debug mode: on
tsp_fc    |  * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
tsp_fc    |  * Restarting with stat
tsp_fc    |  * Debugger is active!
tsp_fc    |  * Debugger PIN: 248-423-277
```
### Example Request

To make a request (i.e. to calculate values of determinant factors assigned to the "tsp-fc" feature collector for a given mobility request defined by a request_id) the command curl can be used:
```bash
$ curl --header 'Content-Type: application/json' \
       --request POST  \
       --data '{"request_id": "123x" }' \
         http://localhost:5001/compute
```
