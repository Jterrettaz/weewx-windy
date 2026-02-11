# Copyright 2019 Matthew Wall  and 2026 Jacques Terrettaz

"""
This is a weewx extension that uploads data to a windy.com

http://windy.com

The protocol is desribed here :

https://stations.windy.com/api-reference

Minimal configuration

[StdRESTful]
    [[Windy]]
        station_id = xxxxxxxxx
        station_password

"""

# deal with differences between python 2 and python 3
try:
    # noinspection PyCompatibility
    from Queue import Queue
except ImportError:
    # noinspection PyCompatibility
    from queue import Queue

try:
    from urllib import urlencode
except ImportError:
    # noinspection PyCompatibility
    from urllib.parse import urlencode

import sys
import time

import weewx
import weewx.manager
import weewx.restx
import weewx.units
from weeutil.weeutil import to_bool


VERSION = "0.8"


try:
    # Test for new-style weewx logging by trying to import weeutil.logger
    import weeutil.logger
    import logging

    log = logging.getLogger(__name__)


    def logdbg(msg):
        log.debug(msg)


    def loginf(msg):
        log.info(msg)


    def logerr(msg):
        log.error(msg)

except ImportError:
    # Old-style weewx logging
    import syslog


    def logmsg(level, msg):
        syslog.syslog(level, 'meteotemplate: %s' % msg)


    def logdbg(msg):
        logmsg(syslog.LOG_DEBUG, msg)


    def loginf(msg):
        logmsg(syslog.LOG_INFO, msg)


    def logerr(msg):
        logmsg(syslog.LOG_ERR, msg)




class Windy(weewx.restx.StdRESTbase):
    DEFAULT_URL = 'https://stations.windy.com/api/v2/observation/update'

    def __init__(self, engine, cfg_dict):
        super(Windy, self).__init__(engine, cfg_dict)
        loginf("version is %s" % VERSION)
        site_dict = weewx.restx.get_site_dict(cfg_dict, 'Windy', 'station_id' , 'station_password')
        if site_dict is None:
            logerr("station_id and station_password are required")
            return
        site_dict.setdefault('server_url', Windy.DEFAULT_URL)

        binding = site_dict.pop('binding', 'wx_binding')
        mgr_dict = weewx.manager.get_manager_dict_from_config(
            cfg_dict, binding)

        self.archive_queue = Queue()
        self.archive_thread = WindyThread(self.archive_queue,
                                          manager_dict=mgr_dict,
                                          **site_dict)

        self.archive_thread.start()
        self.bind(weewx.NEW_ARCHIVE_RECORD, self.new_archive_record)
        loginf("Data will be uploaded to %s" % site_dict['server_url'])

    def new_archive_record(self, event):
        self.archive_queue.put(event.record)


class WindyThread(weewx.restx.RESTThread):

    def __init__(self, q, station_password, station_id, server_url=Windy.DEFAULT_URL,
                 skip_upload=False, manager_dict=None,
                 post_interval=None, max_backlog=sys.maxsize, stale=None,
                 log_success=True, log_failure=True,
                 timeout=60, max_tries=3, retry_wait=5):
        super(WindyThread, self).__init__(q,
                                          protocol_name='Windy',
                                          manager_dict=manager_dict,
                                          post_interval=post_interval,
                                          max_backlog=max_backlog,
                                          stale=stale,
                                          log_success=log_success,
                                          log_failure=log_failure,
                                          max_tries=max_tries,
                                          timeout=timeout,
                                          retry_wait=retry_wait)
        self.password = station_password
        self.station = station_id
        self.server_url = server_url
        self.skip_upload = to_bool(skip_upload)

    def format_url(self,record):
        """Return an URL for doing a POST to windy"""
        url = self.server_url
        if weewx.debug >= 2:
            logdbg("url: %s" % url)
            
        record_m = weewx.units.to_US(record)
        parts = dict()
        parts['ts'] = record['dateTime']
        parts['stationId'] = self.station
        if 'dateTime' in record_m :
            parts['ts'] = record_m ['dateTime']
        if 'outTemp' in record_m :
            parts['tempf'] = record_m ['outTemp']
        if 'windSpeed' in record_m :
            parts['windspeedmph'] = record_m ['windSpeed']
        if 'windDir' in record_m :
            parts['winddir'] = int(record_m ['windDir'])
        if 'windGust' in record_m :
            parts['windgustmph'] = record_m ['windGust']
        if 'outHumidity' in record_m :
            parts['rh'] = record_m ['outHumidity']
        if 'dewpoint' in record_m :
            parts['dewptf'] = record_m ['dewpoint']
        if 'barometer' in record_m :
            parts['baromin'] = record_m ['barometer']
        if 'hourRain' in record_m :
            parts['hourlyrainin'] = record_m ['hourRain'] 
        if 'UV' in record_m:
            parts['uv'] = record_m['UV']
        if 'radiation' in record_m:
            parts['solarradiation'] = record_m['radiation']
        parts['PASSWORD'] = self.password
        logdbg ("%s?%s" % (url, urlencode(parts)))
        return "%s?%s" % (url, urlencode(parts))

    



# Use this hook to test the uploader:
#   PYTHONPATH=bin python bin/user/windy.py

if __name__ == "__main__":
    class FakeMgr(object):
        table_name = 'fake'

        # noinspection PyUnusedLocal,PyMethodMayBeStatic
        def getSql(self, query, value):
            return None


    weewx.debug = 2
    queue = Queue()
    t = WindyThread(queue, station_password='123', station_id='5678')
    r = {'dateTime': int(time.time() + 0.5),
         'usUnits': weewx.US,
         'outTemp': 32.5,
         'inTemp': 75.8,
         'outHumidity': 24,
         'windSpeed': 10,
         'windDir': 32}
    print(t.format_url(r))
    #    print(t.get_post_body(r))
    t.process_record(r, FakeMgr())
