windy - weewx extension that sends data to windy.com
Copyright 2019-2020 Matthew Wall

Modified by Jacques Terrettaz to comply with Windy API v2
Distributed under the terms of the GNU Public License (GPLv3)

You will need your station id and station password from windy.com

  https://stations.windy.com/

Installation instructions:

1) download

wget -O weewx-windy.zip https://github.com/Jterrettaz/weewx-windy/archive/master.zip

2) run the installer

wee_extension --install weewx-windy.zip     for weewx V4 and earlier

weectl extension install weewx-windy.zip

3) enter parameters in the weewx configuration file

[StdRESTful]
    [[Windy]]
        station_id = replace_me
        station_password = replace_me

4) restart weewx


