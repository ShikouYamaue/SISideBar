# -*- coding: utf-8 -*-
import math
            
#内積とる
def dot_poduct(a, b, norm=False):
    if norm:#正規化オプション
        a = normalize(a)
        b = normalize(b)
    dot = (a[0]*b[0])+(a[1]*b[1])
    return dot
    
#ベクトルを正規化して戻す
def normalize(a):
    length = get_length(a)
    return [a[0]/length, a[1]/length]
    
#長さを出す
def get_length(a):
    return math.sqrt(a[0]**2+a[1]**2)