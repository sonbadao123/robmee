import math

def mul4x4_col(a, b):
    res = [0.0]*16
    for col in range(4):
        for row in range(4):
            val = 0.0
            for k in range(4):
                val += a[k*4+row] * b[col*4+k]
            res[col*4+row] = val
    return tuple(res)

def build_vp(cam_pos, yaw_deg, pitch_deg, order='PV', fov_v_deg=60.0, aspect=1920/1080, near=0.3, far=1000.0):
    yaw=math.radians(yaw_deg); pitch=math.radians(pitch_deg)
    cy,sy=math.cos(yaw),math.sin(yaw); cp,sp=math.cos(pitch),math.sin(pitch)
    right=(cy,0.,-sy); up=(sy*sp,cp,cy*sp); forward=(sy*cp,-sp,cy*cp)
    cx,cy_p,cz=cam_pos
    tx2=-(right[0]*cx+right[1]*cy_p+right[2]*cz)
    ty2=-(up[0]*cx+up[1]*cy_p+up[2]*cz)
    tz2=(forward[0]*cx+forward[1]*cy_p+forward[2]*cz)
    V=(right[0],up[0],-forward[0],0.,right[1],up[1],-forward[1],0.,right[2],up[2],-forward[2],0.,tx2,ty2,tz2,1.)
    f=1./math.tan(math.radians(fov_v_deg*0.5)); a=aspect
    P=(f/a,0,0,0, 0,f,0,0, 0,0,-(far+near)/(far-near),-1., 0,0,-2*far*near/(far-near),0)
    if order == 'PV':
        return mul4x4_col(P, V)   # CORRECT
    else:
        return mul4x4_col(V, P)   # BUGGY (old code)

def w2s(pos, m, sw=1920, sh=1080):
    x,y,z=pos
    cx=m[0]*x+m[4]*y+m[8]*z+m[12]
    cy=m[1]*x+m[5]*y+m[9]*z+m[13]
    cw=m[3]*x+m[7]*y+m[11]*z+m[15]
    if cw<0.01: return None
    inv=1./cw
    nx,ny=cx*inv,cy*inv
    return (int(sw*0.5*(1+nx)), int(sh*0.5*(1-ny)))

cam=(5.0, 32.0, -10.0)
vp_ok  = build_vp(cam, 45.0, -15.0, 'PV')
vp_bug = build_vp(cam, 45.0, -15.0, 'VP')

players = [
    ('Left',  (-10.86, 31.45, 43.43)),
    ('Right',  (10.86, 31.45, 43.43)),
    ('Far',    (0.0,   31.45, 150.0)),
]
print('P*V (correct) vs V*P (old bug) for yaw=45 pitch=-15:')
print(f"{'Player':<12} {'CORRECT P*V':<22} {'BUGGY V*P':<22} DIFF")
for name, pos in players:
    ok  = w2s(pos, vp_ok)
    bug = w2s(pos, vp_bug)
    if ok and bug:
        same = ok == bug
        diff = "SAME" if same else "dx=%d dy=%d" % (ok[0]-bug[0], ok[1]-bug[1])
    else:
        diff = "one_none"
    print(f"  {name:<10} {str(ok):<22} {str(bug):<22} {diff}")

print("\nConclusion: when V*P is used instead of P*V, projections are WRONG for rotated cameras.")
print("The static RVA (UnityPlayer+0x2111C90) stores the final P*V computed by Unity — no multiply needed.")
