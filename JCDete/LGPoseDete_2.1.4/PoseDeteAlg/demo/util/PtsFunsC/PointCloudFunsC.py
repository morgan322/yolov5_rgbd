# -*- coding: utf-8 -*-
# cython: language_level=3
"""
author: JiangZhuang
build: 2020/07/28
"""

import os
import sys
import ctypes
import numpy as np

#-------------系统判断-----------------
this_file_path = os.path.abspath(__file__)
if sys.platform == "win32":
    lib_dir = os.path.join(os.path.dirname(this_file_path), 'PointCloudFunsC_Python.dll')
    lib = ctypes.CDLL(lib_dir)
elif sys.platform == "linux":
    lib_dir = os.path.join(os.path.dirname(this_file_path), 'PointCloudFunsC_Python.so')
    lib = ctypes.CDLL(lib_dir)

#-------------创建函数对象-------------
_DepthToPointCloud = lib.DepthToPointCloud
_ReadPointsFromPly = lib.ReadPointsFromPly
_SavePointsToPly = lib.SavePointsToPly
_MatMul = lib.MatMul


class Depth2PointCloud(object):
    def __init__(self, Depth_Height, Depth_Width, cx, cy, fx, fy, factor=1000):
        """
        :param Depth_Height: 深度数据高度
        :param Depth_Width: 深度数据宽度
        :param cx,cy,fx,fy: 相机参数
        :param factor: 相机相对单位(mm)
        """
        Pts_list = [0 for x in range(Depth_Height * Depth_Width * 3)]
        self.cPts = (ctypes.c_float * len(Pts_list))(*Pts_list)

        Param = [cx, cy, fx, fy, factor]
        self.cParam = (ctypes.c_double * len(Param))(*Param)


    def Transformation(self, Depth):
        """
        :param Depth: 深度数据
        :return: 点云数据
        """
        _DepthToPointCloud(Depth.ctypes, Depth.shape[0], Depth.shape[1], self.cParam, self.cPts)
        PointCloud = np.array(self.cPts, dtype=np.float16).reshape([Depth.shape[0] * Depth.shape[1], 3])
        return PointCloud


def ReadPointCloudFromPly(FileName):
    """
    :param FileName: 文件路径
    :param PointsSum: 点总数
    :return: 点云数据
    """
    if sys.platform == "win32":
        cFileName = ctypes.c_char_p(FileName.encode("gbk"))
    elif sys.platform == "linux":
        cFileName = ctypes.c_char_p(FileName.encode("utf-8"))
    with open(FileName, "r") as fp:
        count = 0
        for line in fp.readlines():
            line = line.strip("\n")
            count += 1
            if count == 3:
                break
    ply_3_line_list = line.split(" ")
    Pts_list = [0 for x in range(int(ply_3_line_list[2]) * 3)]
    cPts = (ctypes.c_float * len(Pts_list))(*Pts_list)
    _ReadPointsFromPly(cFileName, cPts)
    PointCloud = np.array(cPts, dtype=np.float32).reshape([int(ply_3_line_list[2]), 3])

    return PointCloud


def SavePointCloudToPly(FileName, Points):
    """
    :param FileName: 文件保存路径
    :param Points: 点云数据
    """
    Points = np.array(Points, dtype=np.float32)
    PointNum = int(Points.shape[0])
    if sys.platform == "win32":
        cFileName = ctypes.c_char_p(FileName.encode("gbk"))
    elif sys.platform == "linux":
        cFileName = ctypes.c_char_p(FileName.encode("utf-8"))
    _SavePointsToPly(cFileName, Points.ctypes, PointNum)


def Rot3D_C(H, Pts):
    """
    :param H: 转换矩阵 (4x4)
    :param Pts: 点云数据 (3x217088)
    :return NewPts: 点云数据 (3x217088)
    """
    tmp = np.row_stack((Pts,np.ones([1, Pts.shape[1]])))
    H = np.asarray(H, dtype=np.float32)
    tmp = np.asarray(tmp, dtype=np.float32)
    NewPts = np.zeros([H.shape[0], tmp.shape[1]], dtype=np.float32)
    _MatMul(H.ctypes, H.shape[0], H.shape[1], tmp.ctypes, tmp.shape[0], tmp.shape[1], NewPts.ctypes)
    return NewPts


def Rot3D(H, Pts):
    """
    :param H: 转换矩阵 (4x4)
    :param Pts: 点云数据 (3x217088)
    :return NewPts: 点云数据 (3x217088)
    """
    tmp = np.row_stack((Pts,np.ones([1, Pts.shape[1]])))
    newpts = np.dot(H,tmp)
    newpts = newpts[0:3, :]
    return newpts