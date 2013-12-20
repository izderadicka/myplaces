'''
Created on Dec 14, 2013

@author: ivan
'''

from myplaces.implaces import LineError

def verify_pos(lng, lat):
    if lng<-180 or lng>180:
        raise LineError(_('Longitude outside range'))
    if lat< -90 or lat>90:
        raise LineError(_('Latitude outside range'))