# -*- encoding: utf-8 -*-
"""
GPS（wgs84）、高德（gcj02）、百度（BD09）三种最常用的地图坐标系之间的相互转换。
"""
import math


class CoordTrans(object):
    x_pi = 3.14159265358979324 * 3000.0 / 180.0
    pi = 3.1415926535897932384626  # π
    a = 6378245.0  # 长半轴
    ee = 0.00669342162296594323  # 偏心率平方
    rf = 1 / (1 - (1 - ee) ** 0.5)  #
    b = a - a / rf
    # ee = 1 - (1 - 1 / rf) ** 2       rf=298.3

    @classmethod
    def gcj02_to_bd09(cls, lng, lat):
        """
        火星坐标系(GCJ-02)转百度坐标系(BD-09)
        谷歌、高德——>百度
        :param lng:火星坐标经度
        :param lat:火星坐标纬度
        :return:
        """
        z = math.sqrt(lng * lng + lat * lat) + 0.00002 * math.sin(lat * cls.x_pi)
        theta = math.atan2(lat, lng) + 0.000003 * math.cos(lng * cls.x_pi)
        bd_lng = z * math.cos(theta) + 0.0065
        bd_lat = z * math.sin(theta) + 0.006
        return [bd_lng, bd_lat]

    @classmethod
    def bd09_to_gcj02(cls, bd_lon, bd_lat):
        """
        百度坐标系(BD-09)转火星坐标系(GCJ-02)
        百度——>谷歌、高德
        :param bd_lat:百度坐标纬度
        :param bd_lon:百度坐标经度
        :return:转换后的坐标列表形式
        """
        x = bd_lon - 0.0065
        y = bd_lat - 0.006
        z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * cls.x_pi)
        theta = math.atan2(y, x) - 0.000003 * math.cos(x * cls.x_pi)
        gg_lng = z * math.cos(theta)
        gg_lat = z * math.sin(theta)
        return [gg_lng, gg_lat]

    @classmethod
    def wgs84_to_gcj02(cls, lng, lat):
        """
        WGS84转GCJ02(火星坐标系)
        :param lng:WGS84坐标系的经度
        :param lat:WGS84坐标系的纬度
        :return:
        """
        if cls.out_of_china(lng, lat):  # 判断是否在国内
            return [lng, lat]
        dlat = cls._transformlat(lng - 105.0, lat - 35.0)
        dlng = cls._transformlng(lng - 105.0, lat - 35.0)
        radlat = lat / 180.0 * cls.pi
        magic = math.sin(radlat)
        magic = 1 - cls.ee * magic * magic
        sqrtmagic = math.sqrt(magic)
        dlat = (dlat * 180.0) / ((cls.a * (1 - cls.ee)) / (magic * sqrtmagic) * cls.pi)
        dlng = (dlng * 180.0) / (cls.a / sqrtmagic * math.cos(radlat) * cls.pi)
        mglat = lat + dlat
        mglng = lng + dlng
        return [mglng, mglat]

    @classmethod
    def gcj02_to_wgs84(cls, lng, lat):
        """
        GCJ02(火星坐标系)转GPS84
        :param lng:火星坐标系的经度
        :param lat:火星坐标系纬度
        :return:
        """
        if cls.out_of_china(lng, lat):
            return [lng, lat]
        dlat = cls._transformlat(lng - 105.0, lat - 35.0)
        dlng = cls._transformlng(lng - 105.0, lat - 35.0)
        radlat = lat / 180.0 * cls.pi
        magic = math.sin(radlat)
        magic = 1 - cls.ee * magic * magic
        sqrtmagic = math.sqrt(magic)
        dlat = (dlat * 180.0) / ((cls.a * (1 - cls.ee)) / (magic * sqrtmagic) * cls.pi)
        dlng = (dlng * 180.0) / (cls.a / sqrtmagic * math.cos(radlat) * cls.pi)
        mglat = lat + dlat
        mglng = lng + dlng
        return [lng * 2 - mglng, lat * 2 - mglat]

    @classmethod
    def bd09_to_wgs84(cls, bd_lon, bd_lat):
        lon, lat = cls.bd09_to_gcj02(bd_lon, bd_lat)
        return cls.gcj02_to_wgs84(lon, lat)

    @classmethod
    def wgs84_to_bd09(cls, lon, lat):
        lon, lat = cls.wgs84_to_gcj02(lon, lat)
        return cls.gcj02_to_bd09(lon, lat)

    @classmethod
    def _transformlat(cls, lng, lat):
        pi = cls.pi
        ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + \
              0.1 * lng * lat + 0.2 * math.sqrt(math.fabs(lng))
        ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 *
                math.sin(2.0 * lng * pi)) * 2.0 / 3.0
        ret += (20.0 * math.sin(lat * pi) + 40.0 *
                math.sin(lat / 3.0 * pi)) * 2.0 / 3.0
        ret += (160.0 * math.sin(lat / 12.0 * pi) + 320 *
                math.sin(lat * pi / 30.0)) * 2.0 / 3.0
        return ret

    @classmethod
    def _transformlng(cls, lng, lat):
        pi = cls.pi
        ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + \
              0.1 * lng * lat + 0.1 * math.sqrt(math.fabs(lng))
        ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 *
                math.sin(2.0 * lng * pi)) * 2.0 / 3.0
        ret += (20.0 * math.sin(lng * pi) + 40.0 *
                math.sin(lng / 3.0 * pi)) * 2.0 / 3.0
        ret += (150.0 * math.sin(lng / 12.0 * pi) + 300.0 *
                math.sin(lng / 30.0 * pi)) * 2.0 / 3.0
        return ret

    @staticmethod
    def out_of_china(lng, lat):
        """
        判断是否在国内，不在国内不做偏移
        :param lng:
        :param lat:
        :return:
        """
        return not (lng > 73.66 and lng < 135.05 and lat > 3.86 and lat < 53.55)


if __name__ == '__main__':
    lng = 128.543
    lat = 37.065
    result1 = CoordTrans.gcj02_to_bd09(lng, lat)
    result2 = CoordTrans.bd09_to_gcj02(lng, lat)
    result3 = CoordTrans.wgs84_to_gcj02(lng, lat)
    result4 = CoordTrans.gcj02_to_wgs84(lng, lat)
    result5 = CoordTrans.bd09_to_wgs84(lng, lat)
    result6 = CoordTrans.wgs84_to_bd09(lng, lat)

    print(result1, result2, result3, result4, result5, result6)
