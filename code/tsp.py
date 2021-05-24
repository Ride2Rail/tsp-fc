#!/usr/bin/env python3
import os
import sys
import pathlib
import logging
import configparser as cp
from r2r_offer_utils  import normalization
from r2r_offer_utils  import cache_operations
from r2r_offer_utils.logging import setup_logger
import isodate
from flask            import Flask, request, abort
import redis

service_name = os.path.splitext(os.path.basename(__file__))[0]
#############################################################################
#############################################################################
#############################################################################
# init Flask
app          = Flask(service_name)
#############################################################################
#############################################################################
#############################################################################
# init config
config = cp.ConfigParser()
config.read(f'{service_name}.conf')
#############################################################################
#############################################################################
#############################################################################
# init cache
cache = redis.Redis(host=config.get('cache', 'host'),
                    port=config.get('cache', 'port'),
                    decode_responses=True)
#############################################################################
#############################################################################
#############################################################################
# init logging
logger, ch = setup_logger()

VERBOSE = int(str(pathlib.Path(config.get('running', 'verbose'))))
SCORES  = str(pathlib.Path(config.get('running',  'scores')))
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
# A method listing out on the screen all keys that are in the cache.
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
# A method executing computations assigned to the tsp-fc feature collector. The tsp-fc feature collector is
# responsible for computation of the following determinant factors: cleanliness", "space_available", "ride_smoothness",
# "seating_quality", "internet_availability", "plugs_or_charging_points", "silence_area_presence", "privacy_level
# and "business_area_presence".
#
# Computation is composed of four phases:
# Phase I:   Extraction of data required by tsp-fc feature collector from the cache. A dedicated procedure defined for
#            this purpose in the unit "cache_operations.py" is utilized.
# Phase II:  Compute values of weights assigned to tsp-fc. For aggregation of data at the tripleg level and for
#            normalization of weights a dedicated procedure implemented in the unit "normalization.py" are utilized.
#            By default "z-scores" are used to normalize data.
# Phase III: Storing the results produced by tsp-fc to cache. A dedicated procedure defined for
# #          this purpose in the unit "cache_operations.py" is utilized.

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
    try:
        output_offer_level, output_tripleg_level = cache_operations.read_data_from_cache_wrapper(
            cache,
            request_id,
            [],
            ["duration", "cleanliness", "space_available",
            "ride_smoothness", "seating_quality", "internet_availability", "plugs_or_charging_points",
            "silence_area_presence", "privacy_level", "user_feedback", "business_area_presence"])
    except redis.exceptions.ConnectionError as exc:
        logging.debug("Reading from cache by tsp-fc feature collector failed.")
        response.status_code = 424
        return response

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
    user_feedback = {}
    business_area_presence = {}

    if "offer_ids" in output_offer_level.keys():
        for offer in output_offer_level["offer_ids"]:
            if "triplegs" in output_tripleg_level[offer].keys():
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
                offer_user_feedback = {}
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
                    offer_user_feedback[tripleg]               = convert_to_float(output_tripleg_level[offer][tripleg]["user_feedback"])
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
                user_feedback[offer]             = normalization.aggregate_a_quantity_over_triplegs(triplegs, temp_duration, offer_user_feedback)
                business_area_presence[offer]    = normalization.aggregate_a_quantity_over_triplegs(triplegs, temp_duration, offer_business_area_presence)
    # calculate zscores
    if SCORES == "minmax_scores":
        # calculate minmax scores
        cleanliness_scores                  = normalization.minmaxscore(cleanliness, flipped=False)
        space_available_scores              = normalization.minmaxscore(space_available, flipped=False)
        ride_smoothness_scores              = normalization.minmaxscore(ride_smoothness, flipped=False)
        seating_quality_scores              = normalization.minmaxscore(seating_quality, flipped=False)
        internet_availability_scores        = normalization.minmaxscore(internet_availability, flipped=False)
        plugs_or_charging_points_scores     = normalization.minmaxscore(plugs_or_charging_points, flipped=False)
        silence_area_presence_scores        = normalization.minmaxscore(silence_area_presence, flipped=False)
        privacy_level_scores                = normalization.minmaxscore(privacy_level, flipped=False)
        user_feedback_scores                = normalization.minmaxscore(user_feedback, flipped=False)
        business_area_presence_scores       = normalization.minmaxscore(business_area_presence, flipped=False)
    else:
        # calculate z-scores
        cleanliness_scores                  = normalization.zscore(cleanliness, flipped=False)
        space_available_scores              = normalization.zscore(space_available, flipped=False)
        ride_smoothness_scores              = normalization.zscore(ride_smoothness, flipped=False)
        seating_quality_scores              = normalization.zscore(seating_quality, flipped=False)
        internet_availability_scores        = normalization.zscore(internet_availability, flipped=False)
        plugs_or_charging_points_scores     = normalization.zscore(plugs_or_charging_points, flipped=False)
        silence_area_presence_scores        = normalization.zscore(silence_area_presence, flipped=False)
        privacy_level_scores                = normalization.zscore(privacy_level, flipped=False)
        user_feedback_scores               = normalization.zscore(user_feedback, flipped=False)
        business_area_presence_scores       = normalization.zscore(business_area_presence, flipped=False)

    if VERBOSE == 1:
        print("cleanliness_scores               = " + str( cleanliness_scores))
        print("space_available_scores           = " + str(space_available_scores))
        print("ride_smoothness_scores           = " + str(ride_smoothness_scores))
        print("seating_quality_scores           = " + str(seating_quality_scores))
        print("internet_availability_scores     = " + str(internet_availability_scores))
        print("plugs_or_charging_points_scores  = " + str(plugs_or_charging_points_scores))
        print("silence_area_presence_scores     = " + str(silence_area_presence_scores))
        print("privacy_level_scores             = " + str(privacy_level_scores))
        print("user_feedback_scores             = " + str(user_feedback_scores))
        print("business_area_presence_scores    = " + str(business_area_presence_scores))
    #
    # III. store the results produced by tsp-fc to cache
    #
    try:
        cache_operations.store_simple_data_to_cache_wrapper(cache, request_id, cleanliness_scores, "cleanliness")
        cache_operations.store_simple_data_to_cache_wrapper(cache, request_id, space_available_scores, "space_available")
        cache_operations.store_simple_data_to_cache_wrapper(cache, request_id, ride_smoothness_scores, "ride_smoothness")
        cache_operations.store_simple_data_to_cache_wrapper(cache, request_id, seating_quality_scores, "seating_quality")
        cache_operations.store_simple_data_to_cache_wrapper(cache, request_id, internet_availability_scores, "internet_availability")
        cache_operations.store_simple_data_to_cache_wrapper(cache, request_id, plugs_or_charging_points_scores, "plugs_or_charging_points")
        cache_operations.store_simple_data_to_cache_wrapper(cache, request_id, silence_area_presence_scores, "silence_area_presence")
        cache_operations.store_simple_data_to_cache_wrapper(cache, request_id, privacy_level_scores, "privacy_level")
        cache_operations.store_simple_data_to_cache_wrapper(cache, request_id, user_feedback_scores, "user_feedback")
        cache_operations.store_simple_data_to_cache_wrapper(cache, request_id, business_area_presence_scores, "business_area_presence")
    except redis.exceptions.ConnectionError as exc:
        logging.debug("Writing outputs to cache by tsp-fc feature collector failed.")

    if VERBOSE == 1:
        print("tsp-fc end")
        print("______________________________")
    return response
#############################################################################
#############################################################################
#############################################################################
if __name__ == '__main__':
    import os

    FLASK_PORT = 5002
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    os.environ["FLASK_ENV"] = "development"
    cache        = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    app.run(port=FLASK_PORT, debug=True)
    exit(0)
