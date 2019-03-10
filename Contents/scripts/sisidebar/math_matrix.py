# -*- coding: utf-8 -*-
from maya import cmds
import math

#numpy使わない行列計算
#逆行列を求める、作成途中あとで
def inv(matrix):
    norm_matrix =[]
    for i, vector in enumerate(matrix):
        norm_vector = [0] * len(vector)
        norm_vector[i] = 1.0
        norm_vector = vector + norm_vector
        norm_matrix.append(norm_vector)
    print norm_matrix
    
#1次元配列の和
def add(a_vector, b_vector):
    if not isinstance(b_vector, list):
        b_vector = [b_vector] * len(a_vector)
    return [a + b for a, b in zip(a_vector, b_vector)]
    
#1次元配列の差
def sub(a_vector, b_vector):
    if not isinstance(b_vector, list):
        b_vector = [b_vector] * len(a_vector)
    return [a - b for a, b in zip(a_vector, b_vector)]
    
#1次元配列に掛け算
def mul(a_vector, b_vector):
    if not isinstance(b_vector, list):
        b_vector = [b_vector] * len(a_vector)
    return [a * b for a, b in zip(a_vector, b_vector)]
    
#行列の掛け算
def dot(a_matrix, b_matrix):
    matrix = []
    for i, a_vector in enumerate(a_matrix):
        array_vector = []
        for k in range(len(b_matrix)):
            value = 0
            for j, a in enumerate(a_vector):
                value += a * b_matrix[j][k]
            array_vector.append(value)
        matrix.append(array_vector)
    return matrix
    
#リシェイプ
def reshape(org_list, shape):
    reshaped_list = []
    for i in range(shape[0]):
        temp_list = []
        for j in range(shape[1]):
            num = org_list.pop(0)
            temp_list.append(num)
        reshaped_list.append(temp_list)
    return reshaped_list