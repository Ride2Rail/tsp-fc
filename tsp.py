#!/usr/bin/env python3
import os
import sys
import pathlib
import logging
import configparser as cp
from r2r_offer_utils  import normalization
from r2r_offer_utils  import cache_operations
import isodate
from flask            import Flask, request, abort
import redis
import json

cache           = redis.Redis(host='cache', port=6379, decode_responses=True)

##### Config
service_basename = os.path.splitext(os.path.basename(__file__))[0]
config_file = '{name}.conf'.format(name=service_basename)
config = cp.ConfigParser()
config.read(config_file)
#####

##### Logging
# create logger
logger = logging.getLogger(service_basename)
logger.setLevel(logging.DEBUG)
# create formatter
formatter_fh = logging.Formatter('[%(asctime)s][%(levelname)s]: %(message)s')
formatter_ch = logging.Formatter('[%(asctime)s][%(levelname)s](%(name)s): %(message)s')
default_log = pathlib.Path(config.get('logging', 'default_log'))
try:
    default_log.parent.mkdir(parents=True, exist_ok=True)
    default_log.touch(exist_ok=True)

    basefh = logging.FileHandler(default_log, mode='a+')
except Exception as err:
    print("WARNING: could not create log file '{log}'"
          .format(log=default_log), file=sys.stderr)
    print("WARNING: {err}".format(err=err), file=sys.stderr)
#####

VERBOSE = int(str(pathlib.Path(config.get('running', 'verbose'))))

#############################################################################
#############################################################################
#############################################################################
def convert_to_float(value):
    if value is not None:
        return float(value)
    else:
        return value
#############################################################################
#############################################################################
#############################################################################
def convert_to_int(value):
    if value is not None:
        return float(value)
    else:
        return value
#############################################################################
#############################################################################
#############################################################################
app = Flask(__name__)
#############################################################################
#############################################################################
#############################################################################
@app.route('/test', methods=['POST'])
def test():
    data       = request.get_json()
    request_id = data['request_id']

    print("Listing cache.")
    for key in cache.scan_iter():
       print(key)

    response   = app.response_class(
        response ='{{"request_id": "{}"}}'.format(request_id),
        status   =200,
        mimetype  ='application/json'
    )
    return response
#############################################################################
#############################################################################
#############################################################################
@app.route('/compute', methods=['POST'])
def extract():
    # import ipdb; ipdb.set_trace()
    data       = request.get_json()
    request_id = data['request_id']

    response   = app.response_class(
        response ='{{"request_id": "{}"}}'.format(request_id),
        status   =200,
        mimetype  ='application/json'
    )
    if VERBOSE== 1:
        print("______________________________")
        print("tsp-fc start")
        print("request_id = " + request_id)

    #
    # I. extract data required by price-fc from cache
    #
    # TODO procedure should be ammeneded to allow for empty list of offer level items
    output_offer_level, output_tripleg_level = cache_operations.extract_data_from_cache(
        cache,
        request_id,
        [],
        #["duration", "cleanliness", "space_available",
         #"ride_smoothness", "seating_quality", "internet_availability", "plugs_or_charging_points",
         #"silence_area_presence", "privacy_level", "business_area_presence"]
     [])

    if VERBOSE == 1:
        print("output_offer_level   = " + str(output_offer_level))
        print("output_tripleg_level = " + str(output_tripleg_level))

    #
    # II. compute values assigned to tsp-fc
    #
    # process TSP data (aggregate TSP data over triplegs using duration information)
    cleanliness = {}
    space_available = {}
    ride_smoothness = {}
    seating_quality = {}
    internet_availability = {}
    plugs_or_charging_points = {}
    silence_area_presence = {}
    privacy_level = {}
    business_area_presence = {}
    for offer in output_offer_level["offer_ids"]:
        triplegs = output_tripleg_level[offer]["triplegs"]
        temp_duration = {}
        offer_cleanliness = {}
        offer_space_available = {}
        offer_ride_smoothness = {}
        offer_seating_quality = {}
        offer_internet_availability = {}
        offer_plugs_or_charging_points = {}
        offer_silence_area_presence = {}
        offer_privacy_level = {}
        offer_business_area_presence = {}
        for tripleg in triplegs:
            temp_duration[tripleg]                     = isodate.parse_duration(output_tripleg_level[offer][tripleg]["duration"]).seconds
            offer_cleanliness[tripleg]                 = convert_to_float(output_tripleg_level[offer][tripleg]["cleanliness"])
            offer_space_available[tripleg]             = convert_to_float(output_tripleg_level[offer][tripleg]["space_available"])
            offer_ride_smoothness[tripleg]             = convert_to_float(output_tripleg_level[offer][tripleg]["ride_smoothness"])
            offer_seating_quality[tripleg]             = convert_to_float(output_tripleg_level[offer][tripleg]["seating_quality"])
            offer_internet_availability[tripleg]       = convert_to_float(output_tripleg_level[offer][tripleg]["internet_availability"])
            offer_plugs_or_charging_points[tripleg]    = convert_to_int(output_tripleg_level[offer][tripleg]["plugs_or_charging_points"])
            offer_silence_area_presence[tripleg]       = convert_to_int(output_tripleg_level[offer][tripleg]["silence_area_presence"])
            offer_privacy_level[tripleg]               = convert_to_float(output_tripleg_level[offer][tripleg]["privacy_level"])
            offer_business_area_presence[tripleg]      = convert_to_float(output_tripleg_level[offer][tripleg]["business_area_presence"])
        # aggregate data over trip legs
        cleanliness[offer]               = normalization.aggregate_a_quantity_over_triplegs(triplegs, temp_duration, offer_cleanliness)
        space_available[offer]           = normalization.aggregate_a_quantity_over_triplegs(triplegs, temp_duration, offer_space_available)
        ride_smoothness[offer]           = normalization.aggregate_a_quantity_over_triplegs(triplegs, temp_duration, offer_ride_smoothness)
        seating_quality[offer]           = normalization.aggregate_a_quantity_over_triplegs(triplegs, temp_duration, offer_seating_quality)
        internet_availability[offer]     = normalization.aggregate_a_quantity_over_triplegs(triplegs, temp_duration, offer_internet_availability)
        plugs_or_charging_points[offer]  = normalization.aggregate_a_quantity_over_triplegs(triplegs, temp_duration, offer_plugs_or_charging_points)
        silence_area_presence[offer]     = normalization.aggregate_a_quantity_over_triplegs(triplegs, temp_duration, offer_silence_area_presence)
        privacy_level[offer]             = normalization.aggregate_a_quantity_over_triplegs(triplegs, temp_duration, offer_privacy_level)
        business_area_presence[offer]    = normalization.aggregate_a_quantity_over_triplegs(triplegs, temp_duration, offer_business_area_presence)

    # calculate zscores
    cleanliness_z_scores             = normalization.zscore(cleanliness, flipped=False)
    space_available_z_scores         = normalization.zscore(space_available, flipped=False)
    ride_smoothness_z_scores         = normalization.zscore(ride_smoothness, flipped=False)
    seating_quality_z_scores         = normalization.zscore(seating_quality, flipped=False)
    internet_availability_z_scores   = normalization.zscore(internet_availability, flipped=False)
    plugs_or_charging_points_z_scores= normalization.zscore(plugs_or_charging_points, flipped=False)
    silence_area_presence_z_scores   = normalization.zscore(silence_area_presence, flipped=False)
    privacy_level_z_scores           = normalization.zscore(privacy_level, flipped=False)
    business_area_presence_z_scores  = normalization.zscore(business_area_presence, flipped=False)

    if VERBOSE == 1:
        print("cleanliness_z_scores      = " + str( cleanliness_z_scores))
        print("space_available_z_scores      = " + str(space_available_z_scores))
        print("ride_smoothness_z_scores      = " + str(ride_smoothness_z_scores))
        print("seating_quality_z_scores      = " + str(seating_quality_z_scores))
        print("internet_availability_z_scores      = " + str(internet_availability_z_scores))
        print("plugs_or_charging_points_z_scores      = " + str(plugs_or_charging_points_z_scores))
        print("silence_area_presence_z_scores     = " + str(silence_area_presence_z_scores))
        print("privacy_level_z_scores      = " + str(privacy_level_z_scores))
        print("business_area_presence_z_scores      = " + str(business_area_presence_z_scores))
    #
    # IV. store the results produced by price-fc to cache
    #
    cache_operations.store_simple_data_to_cache(cache, request_id, cleanliness_z_scores, "cleanliness")
    cache_operations.store_simple_data_to_cache(cache, request_id, space_available_z_scores, "space_available")
    cache_operations.store_simple_data_to_cache(cache, request_id, ride_smoothness_z_scores, "ride_smoothness")
    cache_operations.store_simple_data_to_cache(cache, request_id, seating_quality_z_scores, "seating_quality")
    cache_operations.store_simple_data_to_cache(cache, request_id, internet_availability_z_scores, "internet_availability")
    cache_operations.store_simple_data_to_cache(cache, request_id, plugs_or_charging_points_z_scores, "plugs_or_charging_points")
    cache_operations.store_simple_data_to_cache(cache, request_id, silence_area_presence_z_scores, "silence_area_presence")
    cache_operations.store_simple_data_to_cache(cache, request_id, privacy_level_z_scores, "privacy_level")
    cache_operations.store_simple_data_to_cache(cache, request_id, business_area_presence_z_scores, "business_area_presence")

    if VERBOSE == 1:
        print("tsp-fc end")
        print("______________________________")
    return response
#############################################################################
#############################################################################
#############################################################################
if __name__ == '__main__':
    import os

    FLASK_PORT = 5001
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    os.environ["FLASK_ENV"] = "development"
    cache        = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    app.run(port=FLASK_PORT, debug=True)
    exit(0)


