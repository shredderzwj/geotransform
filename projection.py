# -*- encoding: utf-8 -*-
"""
中国常用大地测量（投影）坐标系转换（标准转换，不涉及使用7参数平移、旋转、缩放）。
主要有wgs84、西安80、北京54、新北京、cgcs2000等我国常用坐标系之间的相互转换。
本模块是对 pyproj 中的相关方法进行了二次封装，以方便使用！采用epsg中记录的各个坐标系参数
pyproj 官方文档：http://pyproj4.github.io/pyproj/stable/
note：pyproj 通过 crs 生成transformer 是非常耗时的操作，经测试
    AMD Ryzen 5 2500U with Radeon Vega Mobile G方向 2.00GHz平台，
    创建一个需要0.2~0.3秒。在批量转换的任务中，如果对每个点生成一个transformer，效率是不能接受的！
    考虑到，一个确定的转换任务中，需要重新生成transformer的地方在：输入点位于不同投影分度带。
    这里采用的策略是借助单例设计模式的思想，在批量转换的时候，先获取某个点转换的特征：
        1、输入坐标projection
        2、输入坐标中央经线
        3、输入坐标是否带有分度带带号
        4、输出坐标的projection
        5、输出坐标中央经线
        6、输出坐标是否带有分度带带号
    根据这些特征可以唯一的描述一个transformer，可以根据这些特征，生成一个transformer_key，
    用transformer_key作为键将transformer对象保存至字典中，在生成transformer之前检查拥有此特征的transformer是否已经生成，
    如果已经生成则直接返回，如果未生成，则生成。
    因为每次批量转换的任务所涉及的范围一般不会跨几个分度带，因此不会生成特别多的transformer，所以空间占用和
    整体的时间效率都能接受。
"""
from pyproj import Transformer, CRS
    
    
class Epsg(object):
    """
    获取CRS（coordinate reference system）
    类方法的名称有特殊含义，后续计算需要用到方法名。
    所有获取CRS的类方法均有以下两个参数，其中当CRS为经纬度坐标时，这两个参数仅为占位参数，
    不起任何作用，只是为了参数统一方便回调：
        lng：float 坐标经度或者坐标点所在分度带的中央经线值（用来确定坐标点所在分度带号，以返回正确的CRS）
        with_zone：指定坐标是否带有所在分度带的带号，默认为False（True：带有带号，False：不带）
    """
    @staticmethod
    def crs(epsg_code, index=None, lng_0=None):
        crs = CRS.from_epsg(epsg_code)
        crs.index = index
        crs.lng_0 = lng_0
        return crs

    @staticmethod
    def calc_number(lng, zone_degree):
        return int(lng / zone_degree + zone_degree / 6)  # 带号

    @classmethod
    def calc_number_lng0(cls, lng, zone_degree):
        number = cls.calc_number(lng, zone_degree)
        return number, (number - 1) * zone_degree + 3  # （带号，中央经度）

    @classmethod
    def __gauss_base(cls, lng, zone_degree, code, with_zone_code, with_zone=False):
        number, lng_0 = cls.calc_number_lng0(lng, zone_degree)
        i = number - int(75 / zone_degree + zone_degree / 6)
        if lng_0 - zone_degree / 2 <= lng < lng_0 + zone_degree / 2:
            if with_zone:
                epsg = i + with_zone_code
            else:
                epsg = i + code
            return cls.crs(epsg, number, lng_0)
        raise ValueError('lng 取值范围为：73.5~136.5')

    @classmethod
    def wgs84(cls, *args, **kwargs):
        return cls.crs(4326)

    @classmethod
    def wgs84_3d(cls, *args, **kwargs):
        return cls.crs(4979)

    @classmethod
    def xian80(cls, *args, **kwargs):
        return cls.crs(4610)

    @classmethod
    def bj_new(cls, *args, **kwargs):
        return cls.crs(4555)

    @classmethod
    def cgcs2000(cls, *args, **kwargs):
        return cls.crs(4490)

    @classmethod
    def xian80_gauss_3(cls, lng, with_zone=False):
        return cls.__gauss_base(lng, 3, 2370, 2349, with_zone)

    @classmethod
    def xian80_gauss_6(cls, lng, with_zone=False):
        return cls.__gauss_base(lng, 6, 2338, 2327, with_zone)

    @classmethod
    def bj54_gauss_3(cls, lng, with_zone=False):
        return cls.__gauss_base(lng, 3, 2422, 2401, with_zone)

    @classmethod
    def bj_new_gauss_3(cls, lng, with_zone=False):
        zone_degree = 3
        number = int(lng / zone_degree + zone_degree / 6)  # 带号
        lng_0 = (number - 1) * zone_degree + 3  # 中央经度
        i = number - int(75 / zone_degree + zone_degree / 6)
        if lng_0 - zone_degree / 2 <= lng < lng_0 + zone_degree / 2:
            if with_zone:
                if lng_0 <= 87:
                    epsg = i + 4652
                else:
                    epsg = i + 4761
            else:
                if lng_0 <= 129:
                    epsg = i + 4782
                elif lng_0 == 132:
                    epsg = 4812
                else:
                    epsg = 4822
            return cls.crs(epsg, number, lng_0)
        raise ValueError('lng 取值范围为：73.5~136.5')

    @classmethod
    def bj_new_gauss_6(cls, lng, with_zone=False):
        return cls.__gauss_base(lng, 6, 4579, 4568, with_zone)

    @classmethod
    def cgcs2000_gauss_3(cls, lng, with_zone=False):
        return cls.__gauss_base(lng, 3, 4534, 4513, with_zone)

    @classmethod
    def cgcs2000_gauss_6(cls, lng, with_zone=False):
        return cls.__gauss_base(lng, 6, 4502, 4491, with_zone)


class TransProj(object):
    """经纬坐标转换为其他坐标"""
    epsg = Epsg

    def __init__(self,
        exist_proj=None, exist_lng0=None, exist_with_zone=False,
        target_proj=None, target_lng0=None, target_with_zone=False,
        transformer=None
    ):
        """
        :param exist_proj: function 获取原有坐标坐标系 epsg 代码的回调函数（Epsg类方法）
        :param exist_lng0: float 输入坐标点的中央经线经度值，不指定此值，将根据输入的值自动计算。
                            当输入坐标为投影坐标并且不带分度带带号时，必须指定此值！
        :param exist_with_zone: Boolean 输入坐标是否带有分度带的带号
        :param target_proj: function 获取目标坐标坐标系 epsg 代码的回调函数（Epsg类方法）
        :param target_lng0: float 输出坐标点的中央经线经度值，不指定此值，将根据输入的值自动计算。
                            注意！！！
                            保险起见，在转换经度跨度不大的批量转换时建议均指定此值，因为在批量计算中，由于点集可能位于分度带
                            的中央经线周围，中央经线的自动计算是严格按照分度带的规定计算的，在输出投影坐标不加带号的情况下，
                            转换后的坐标可能分不清位于哪个分度带内，导致转换后坐标点使用麻烦（某些点可能会偏移一个分度带，
                            还需找出这些点重新指定分度带，再解算回去），因此为了统一，建议在一次批量转换过程中指定中央经线
                            并记录此值。
        :param target_with_zone: Boolean 输出坐标是否带有分度带的带号
        :param transformer: obj pyproj.transformer.Transformer 自定义的转换器。
                            当此参数赋值时，前面所有的参数将不起作用，因为前面所有参数是用来创建转换器用的
        """
        self.exist_proj = exist_proj
        self.exist_with_zone = exist_with_zone
        self.exist_lng0 = exist_lng0
        self.target_proj = target_proj
        self.target_with_zone = target_with_zone
        self.target_lng0 = target_lng0
        self._transformer = transformer
        if exist_proj is None and transformer is None:
            self.transformer = Transformer.from_pipeline('proj=noop ellps=GRS80')
        # 保存已经存在的转换器
        self.transformers = {}

    def transformer(self, coordinate):
        """
        创建坐标转换的 transformer
        :param coordinate: list or tuple 坐标
        :return: obj pyproj.transformer.Transformer 对象。
        """
        lng = coordinate[0]
        if self._transformer:
            return self._transformer

        exist_proj_name = getattr(self.exist_proj, '__name__')
        target_proj_name = getattr(self.target_proj, '__name__')
        exist_zone_degree = None
        target_zone_degree = None

        try:
            exist_zone_degree = int(exist_proj_name.split('_')[-1])
        except Exception:
            pass

        try:
            target_zone_degree = int(target_proj_name.split('_')[-1])
        except Exception:
            pass

        # 确定输入坐标的中央经度，当创建对象的时候指定了中央经线，则使用指定的
        if self.exist_lng0:
            try:
                exist_lng0 = float(self.exist_lng0)
            except Exception:
                raise TypeError('指定输入中央经线经度值错误！')
        else:
            if exist_zone_degree:
                # 说明输入的是投影坐标
                if self.exist_with_zone:
                    number = int(lng / 1000000)
                    exist_lng0 = (number - 1) * exist_zone_degree + 3
                else:
                    raise TypeError('当原有坐标不是经纬度坐标并且输入投影坐标X方向没有带号时，创建对象时必须指定正确的中央经线经度值！')
            else:
                # 说明输入的是经纬度坐标
                exist_lng0 = lng

        # 确定输出坐标的中央经度,当没有指定的时候，使用输入的
        if self.target_lng0:
            try:
                target_lng0 = float(self.target_lng0)
            except Exception:
                raise TypeError('指定输出中央经线经度值错误！')
        else:
            target_lng0 = exist_lng0

        # 格式化中央经度 ，以获得每个分度带内的 transformer_key
        if exist_zone_degree:
            exist_lng0 = Epsg.calc_number_lng0(exist_lng0, exist_zone_degree)[-1]
        else:
            exist_lng0 = None

        if target_zone_degree:
            target_lng0 = Epsg.calc_number_lng0(target_lng0, target_zone_degree)[-1]
        else:
            target_lng0 = None

        transformer_key = "{}/{}/{}/{}/{}/{}".format(
            exist_proj_name, str(exist_lng0), str(self.exist_with_zone),
            target_proj_name, str(target_lng0), str(self.target_with_zone),
        )

        if transformer_key in self.transformers:
            return self.transformers[transformer_key]

        # 生成transformer
        transformer = Transformer.from_crs(
            self.exist_proj(exist_lng0, self.exist_with_zone),
            self.target_proj(target_lng0, self.target_with_zone),
            always_xy=True
        )
        # print('生成trans：', transformer_key)
        self.transformers[transformer_key] = transformer
        return transformer

    def __call__(self, coordinate, *args, **kwargs):
        transformer = self.transformer(coordinate)
        # print(transformer.definition)
        return transformer.transform(*coordinate)


if __name__ == '__main__':
    import time

    with open('test.csv') as fp:
        data = fp.read()
    coords = [tuple(map(lambda _: float(_), x.split(','))) for x in data.split('\n') if x]

    start_time = time.time()
    trans = TransProj(exist_proj=Epsg.wgs84_3d, target_proj=Epsg.xian80_gauss_3, exist_lng0=114, target_with_zone=True)
    new_coords = []
    for coord in coords:
        new_coord = trans(coord)
        new_coords.append(new_coord)

    print('转换点数：%d，耗时：%.3fS' % (len(new_coords), time.time() - start_time))
    print("生成 transformer 个数：%d" % len(trans.transformers))
    for t in trans.transformers.values():
        print('\t', t.description)

    with open('test_result.csv', 'w') as f:
        for x in new_coords:
            f.write('%.3f,%.3f,%.3f\n' % tuple(x))
