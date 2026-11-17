import sys, math
sys.path.append(r'd:\ESP robrun')

def build_vp(cam_pos, yaw_deg, pitch_deg, fov_v_deg=60.0, aspect=1920/1080, near=0.3, far=1000.0):
    yaw   = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    right   = ( cy,    0.0, -sy)
    up      = ( sy*sp,  cp,  cy*sp)
    forward = ( sy*cp, -sp,  cy*cp)
    cx, cy_p, cz = cam_pos
    tx2 = -(right[0]*cx    + right[1]*cy_p  + right[2]*cz)
    ty2 = -(up[0]*cx       + up[1]*cy_p     + up[2]*cz)
    tz2 =  (forward[0]*cx  + forward[1]*cy_p + forward[2]*cz)
    V = (right[0], up[0], -forward[0], 0.0,
         right[1], up[1], -forward[1], 0.0,
         right[2], up[2], -forward[2], 0.0,
         tx2,      ty2,   tz2,         1.0)
    f = 1.0 / math.tan(math.radians(fov_v_deg*0.5))
    a = aspect
    P = (f/a, 0, 0, 0,  0, f, 0, 0,  0, 0, -(far+near)/(far-near), -1.0,  0, 0, -2*far*near/(far-near), 0)
    def mul4x4(a_m, b_m):
        res = [0.0]*16
        for col in range(4):
            for row in range(4):
                val = 0.0
                for k in range(4):
                    val += a_m[k*4+row] * b_m[col*4+k]
                res[col*4+row] = val
        return tuple(res)
    return mul4x4(P, V)

def w2s_new(pos, m, sw=1920, sh=1080):
    x, y, z = pos
    clip_x = m[0]*x + m[4]*y + m[8]*z  + m[12]
    clip_y = m[1]*x + m[5]*y + m[9]*z  + m[13]
    clip_w = m[3]*x + m[7]*y + m[11]*z + m[15]
    if clip_w < 0.01: return None
    inv = 1.0/clip_w
    nx, ny = clip_x*inv, clip_y*inv
    return (int(sw*0.5*(1+nx)), int(sh*0.5*(1-ny)))

def w2s_old(pos, m, sw=1920, sh=1080):
    x, y, z = pos
    if abs(m[11]) > 0.0001:
        w  = m[3]*x  + m[7]*y  + m[11]*z + m[15]
        sx = m[0]*x  + m[4]*y  + m[8]*z  + m[12]
        sy = m[1]*x  + m[5]*y  + m[9]*z  + m[13]
    else:
        w  = m[12]*x + m[13]*y + m[14]*z + m[15]
        sx = m[0]*x  + m[1]*y  + m[2]*z  + m[3]
        sy = m[4]*x  + m[5]*y  + m[6]*z  + m[7]
    if w < 0.01: return None
    inv = 1.0/w
    nx, ny = sx*inv, sy*inv
    cxx, cyy = sw*0.5, sh*0.5
    return (int(cxx + nx*cxx), int(cyy - ny*cyy))

cam = (5.0, 32.0, -10.0)
vp = build_vp(cam, yaw_deg=45.0, pitch_deg=-15.0)

print("Camera yaw=45 pitch=-15 at (5,32,-10)")
print(f"{'Player':<20} {'NEW(col-maj)':<22} {'OLD(buggy)':<22} DIFF")
players = [
    ("Left",  (-10.86, 31.45, 43.43)),
    ("Right",  (10.86, 31.45, 43.43)),
    ("Far",    (0.0,   31.45, 150.0)),
    ("Close",  (2.0,   32.0,    5.0)),
]
for name, pos in players:
    n = w2s_new(pos, vp)
    o = w2s_old(pos, vp)
    if n and o:
        diff = "SAME" if n == o else f"DIFFER dx={n[0]-o[0]} dy={n[1]-o[1]}"
    else:
        diff = "one_returned_None"
    print(f"  {name:<18} {str(n):<22} {str(o):<22} {diff}")

# The key difference: for a rotated camera where clip_w != row-major w,
# the old code picks the WRONG w term. Show the raw terms:
print("\nRaw clip terms for 'Left' player:")
x, y, z = -10.86, 31.45, 43.43
m = vp
print(f"  clip_x (col-maj) = {m[0]*x + m[4]*y + m[8]*z  + m[12]:.4f}")
print(f"  clip_y (col-maj) = {m[1]*x + m[5]*y + m[9]*z  + m[13]:.4f}")
print(f"  clip_w (col-maj) = {m[3]*x + m[7]*y + m[11]*z + m[15]:.4f}")
# Old code when abs(m[11])>0.0001 (which IS the case for perspective):
print(f"  clip_w (old, same formula) = {m[3]*x + m[7]*y + m[11]*z + m[15]:.4f}")
# Old code ELSE branch:
print(f"  w_old_else_branch = {m[12]*x + m[13]*y + m[14]*z + m[15]:.4f}")
print(f"  sx_old_else = {m[0]*x + m[1]*y + m[2]*z + m[3]:.4f}")
print(f"  sy_old_else = {m[4]*x + m[5]*y + m[6]*z + m[7]:.4f}")
print("\n  NOTE: The old if-branch actually uses the same formula as the new code for")
print("  clip_w and clip_x/y when abs(m[11])>0.0001 (perspective matrix signature).")
print("  So for a pure VP matrix the old code IS correct too in the if-branch.")
print("  The bug was in _read_camera_matrix: multiplying V*P instead of P*V.")
print("  With wrong VP order, the terms map differently and produce wrong screen coords.")
