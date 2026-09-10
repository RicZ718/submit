# -*- coding: utf-8 -*-
"""
电路②  戴维南定理验证 (Thevenin Theorem verification)

含源二端网络 (self-defined):
    V_s = 10 V,  R1 = 4 kΩ,  R2 = 6 kΩ
    端口为 R2 两端 (节点 a 与地)。

手算:
    V_th = V_oc = V_s * R2/(R1+R2) = 10*6/10 = 6 V
    R_th = R1 || R2 = 4k || 6k = 2.4 kΩ
    I_sc = V_th / R_th = 6 / 2.4k = 2.5 mA
    等效电路接负载 RL = 1.2 kΩ:
        I_L = V_th/(R_th+RL) = 6/(2.4k+1.2k) = 1.667 mA
        V_L = I_L * RL = 2 V

仿真内容:
    - 画原网络原理图 (标注端口) 与 等效电路图
    - 测开路电压 V_oc  (op)
    - 测短路电流 I_sc  (op, 0V 电压表)
    - R_th = V_oc/I_sc
    - 负载验证: 原网络接 RL  vs  等效电路接 RL, 对比 V_L, I_L
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import schemdraw
import schemdraw.elements as elm

import PySpice.Logging.Logging as L
L.setup_logging(logging_level='ERROR')
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

# ---------------- 元件参数 ----------------
Vs = 10 @ u_V
R1 = 4 @ u_kΩ
R2 = 6 @ u_kΩ
RL = 1.2 @ u_kΩ

# 手算
Vth_theory = float(Vs) * float(R2) / (float(R1) + float(R2))          # 6 V
Rth_theory = float(R1) * float(R2) / (float(R1) + float(R2))          # 2400 ohm
Rth_kohm = Rth_theory / 1000                                           # 2.4 kΩ
Isc_theory = Vth_theory / Rth_theory * 1000                            # mA
IL_theory = Vth_theory / (Rth_theory + float(RL)) * 1000               # mA
VL_theory = IL_theory / 1000 * float(RL)                               # V
print('【戴维南定理验证】')
print('  V_s=10V, R1=4k, R2=6k, RL=1.2k')
print('  手算 V_th = V_oc = %.2f V' % Vth_theory)
print('  手算 R_th = R1||R2 = %.2f kΩ' % Rth_kohm)
print('  手算 I_sc = %.3f mA' % Isc_theory)
print('  手算负载 I_L = %.3f mA, V_L = %.3f V' % (IL_theory, VL_theory))


def scalar(wf):
    return float(np.asarray(wf).ravel()[0])

# ---------------- 画原网络原理图 ----------------
d = schemdraw.Drawing(show=False)
d.config(unit=2, fontsize=11)
d += elm.SourceV().label('V_s\n10 V', loc='left').up().at((0, 0))
d += (elm.Resistor().label('R1 4k', loc='top').right().at((0, 2)))
d += elm.Dot().at((2, 2))                       # 节点 a (端口 +)
d += (elm.Resistor().label('R2 6k', loc='right').down().at((2, 2)))
d += elm.Line().down().length(1)
d += elm.Ground()
d += elm.Line().at((0, 0)).down().length(2)
d += elm.Ground()
# 端口标注
d += (elm.Line().up().length(1.0).at((2, 2)))
d += (elm.Dot(open=True).at((2, 3)))
d += elm.Label().at((2.4, 3.1)).label('a  (port +)')
d += elm.Label().at((2.2, -1.1)).label('b  (port -)')
d.save('figures/thevenin_network.png')
print('  已保存原网络图: figures/thevenin_network.png')

# ---------------- 画等效电路图 ----------------
d2 = schemdraw.Drawing(show=False)
d2.config(unit=2, fontsize=11)
d2 += elm.SourceV().label('V_th\n6 V', loc='left').up().at((0, 0))
d2 += (elm.Resistor().label('R_th 2.4k', loc='top').right().at((0, 2)))
d2 += (elm.Resistor().label('R_L 1.2k', loc='right').down().at((2, 2)))
d2 += elm.Line().down().length(1)
d2 += elm.Ground()
d2 += elm.Line().at((0, 0)).down().length(2)
d2 += elm.Ground()
d2 += (elm.Line().up().length(1.0).at((2, 2)))
d2 += elm.Dot(open=True).at((2, 3))
d2 += elm.Label().at((2.4, 3.1)).label('a  (load port)')
d2.save('figures/thevenin_equiv.png')
print('  已保存等效电路图: figures/thevenin_equiv.png')

# ================= 仿真 1: 开路电压 V_oc =================
c1 = Circuit('voc')
c1.V('src', 'p', c1.gnd, Vs)
c1.R('R1', 'p', 'a', R1)
c1.R('R2', 'a', c1.gnd, R2)
sim1 = c1.simulator(temperature=25, nominal_temperature=25)
op1 = sim1.operating_point()
Voc_sim = scalar(op1['a'])
print('  仿真 V_oc = %.4f V' % Voc_sim)

# ================= 仿真 2: 短路电流 I_sc =================
# 用 0V 电压表从 a 到地测短路电流
c2 = Circuit('isc')
c2.V('src', 'p', c2.gnd, Vs)
c2.R('R1', 'p', 'a', R1)
c2.R('R2', 'a', c2.gnd, R2)
c2.V('meter', 'a', c2.gnd, 0 @ u_V)      # 0V 源 = 电流表 (短路)
sim2 = c2.simulator(temperature=25, nominal_temperature=25)
op2 = sim2.operating_point()
Isc_sim = scalar(op2.branches['vmeter']) * 1000     # mA (正方向从 a 到 gnd)
print('  仿真 I_sc = %.4f mA' % Isc_sim)

Rth_sim = Voc_sim / (Isc_sim / 1000) / 1000         # kΩ
print('  仿真 R_th = V_oc/I_sc = %.4f kΩ' % Rth_sim)

# ================= 仿真 3: 原网络接负载 =================
c3 = Circuit('orig_load')
c3.V('src', 'p', c3.gnd, Vs)
c3.R('R1', 'p', 'a', R1)
c3.R('R2', 'a', c3.gnd, R2)
c3.R('RL', 'a', c3.gnd, RL)
sim3 = c3.simulator(temperature=25, nominal_temperature=25)
op3 = sim3.operating_point()
VL_orig = scalar(op3['a'])
IL_orig = VL_orig / float(RL) * 1000               # mA
print('  原网络接 RL: V_L = %.4f V, I_L = %.4f mA' % (VL_orig, IL_orig))

# ================= 仿真 4: 等效电路接负载 =================
c4 = Circuit('thev_load')
c4.V('th', 'p', c4.gnd, Vth_theory @ u_V)
c4.R('Rth', 'p', 'a', Rth_kohm @ u_kΩ)
c4.R('RL', 'a', c4.gnd, RL)
sim4 = c4.simulator(temperature=25, nominal_temperature=25)
op4 = sim4.operating_point()
VL_eq = scalar(op4['a'])
IL_eq = VL_eq / float(RL) * 1000                    # mA
print('  等效电路接 RL: V_L = %.4f V, I_L = %.4f mA' % (VL_eq, IL_eq))

# ---------------- 对比表 ----------------
print('\n================ 手算 vs 仿真 对比 ================')
print('  V_oc: 手算 %.4f V | 仿真 %.4f V | 偏差 %.3f%%'
      % (Vth_theory, Voc_sim, abs(Voc_sim - Vth_theory) / Vth_theory * 100))
print('  I_sc: 手算 %.4f mA | 仿真 %.4f mA | 偏差 %.3f%%'
      % (Isc_theory, Isc_sim, abs(Isc_sim - Isc_theory) / Isc_theory * 100))
print('  R_th: 手算 %.4f kOhm | 仿真 (V_oc/I_sc) %.4f kOhm | 偏差 %.3f%%'
      % (Rth_kohm, Rth_sim, abs(Rth_sim - Rth_kohm) / Rth_kohm * 100))
print('  负载V_L: 手算 %.4f V | 原网络 %.4f V | 等效电路 %.4f V'
      % (VL_theory, VL_orig, VL_eq))
print('  负载I_L: 手算 %.4f mA | 原网络 %.4f mA | 等效电路 %.4f mA'
      % (IL_theory, IL_orig, IL_eq))

# ---------------- 结果写入 UTF-8 txt ----------------
with open('figures/thevenin_results.txt', 'w', encoding='utf-8') as fh:
    fh.write('戴维南定理验证 结果\n')
    fh.write('Vs=10V R1=4k R2=6k RL=1.2k\n')
    fh.write('Vth_theory_v=%.4f\n' % Vth_theory)
    fh.write('Voc_sim_v=%.4f\n' % Voc_sim)
    fh.write('Rth_theory_kohm=%.4f\n' % Rth_kohm)
    fh.write('Rth_sim_kohm=%.4f\n' % Rth_sim)
    fh.write('Isc_theory_ma=%.4f\n' % Isc_theory)
    fh.write('Isc_sim_ma=%.4f\n' % Isc_sim)
    fh.write('VL_theory_v=%.4f\n' % VL_theory)
    fh.write('VL_orig_v=%.4f\n' % VL_orig)
    fh.write('VL_eq_v=%.4f\n' % VL_eq)
    fh.write('IL_theory_ma=%.4f\n' % IL_theory)
    fh.write('IL_orig_ma=%.4f\n' % IL_orig)
    fh.write('IL_eq_ma=%.4f\n' % IL_eq)
print('  已写入结果文件: figures/thevenin_results.txt')
