import numpy as np

def q3_1(a, b, dist):
    a, b = np.array(a, dtype=np.float64), np.array(b, dtype=np.float64)
    aw, bw = a[3], b[3]
    adw, bdw = a / aw, b / bw
    adw[3] = 1 / aw
    bdw[3] = 1 / bw
    c = adw * (1-dist) + bdw * dist
    cw = c[3]
    d = c[4:] / cw
    return c[:3], 1 / cw, d
    
FRUSTUM = np.array([1,0,0,1,-1,0,0,1,0,1,0,1,0,-1,0,1,0,0,1,1,0,0,-1,1])
FRUSTUM.resize((6, 4))
def q3_2(a, b):
    a, b = np.array(a, dtype=np.float64), np.array(b, dtype=np.float64)
    dist_a, dist_b = np.dot(FRUSTUM, a), np.dot(FRUSTUM, b)
    dim_a = [c for c, i in enumerate(dist_a) if i < 0]
    dim_b = [c for c, i in enumerate(dist_b) if i < 0]
    if dim_b:
        a, b = b, a
    dim = (dim_a or dim_b)[0]
    p = (dist_b[dim] * a - dist_a[dim] * b) / (dist_b[dim] - dist_a[dim])
    t = (a[2] - p[2]) / (a[2] + b[2])
    return dim, t

def q3_3(source, dest):
    source, dest = np.array(source, dtype=np.float64), np.array(dest, dtype=np.float64)
    source_alpha, dest_alpha = source[3], dest[3]
    new_alpha = source_alpha + dest_alpha - (dest_alpha * source_alpha)
    pm_rgb = source_alpha * source + (1 - source_alpha) * dest_alpha * dest
    new_rgb = pm_rgb / new_alpha if new_alpha > 0.0 else None
    return new_alpha, new_rgb
