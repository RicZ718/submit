# -*- coding: utf-8 -*-
"""
电路③  NMOS 共源级放大电路 (Common-Source amplifier)

电路参数 (题目给定):
    VDD = 5 V, Rg1 = 60 kΩ, Rg2 = 40 kΩ, Rd = 2 kΩ, Cb1 足够大
    NMOS: K = 0.8 mA/V^2, Vth = 1 V, λ = 0.02 /V
    输入 Vi = 10 mV / 1 kHz 正弦波

NGSPICE level-1 模型换算:
    Id = 0.5*KP*(W/L)*(Vgs-Vth)^2*(1+λ*Vds)
    令 0.5*KP*(W/L) = K = 0.8mA/V^2, 取 W/L = 1 => KP = 1.6 mA/V^2
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import schemdraw
import schemdraw.elements as elm

import PySpice.Logging.Logging as L
L.setup_logging(logging_level='ERROR')
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

# ---------------- 电路参数 ----------------
VDD = 5 @ u_V
Rg1 = 60 @ u_kΩ
Rg2 = 40 @ u_kΩ
Rd = 2 @ u_kΩ
Cb1 = 10 @ u_uF          # 足够大
K = 0.8e-3               # mA/V^2 -> A/V^2
Vth = 1.0                # V
LAMBDA = 0.02            # 1/V
Vi_amp = 10e-3           # V (10 mV)
f_in = 1e3               # Hz

def scalar(wf):
    return float(np.asarray(wf).ravel()[0])

# ================= 手算 =================
VG = float(VDD) * float(Rg2) / (float(Rg1) + float(Rg2))    # 2 V
VGS = VG                                                     # 源接地 => VGS = VG
A = K * (VGS - Vth) ** 2                                     # Id0 = K*(Vgs-Vth)^2 (不含λ)
ID = A * (1 + LAMBDA * float(VDD)) / (1 + A * LAMBDA * float(Rd))
VDS = float(VDD) - ID * float(Rd)
gm_th = 2 * K * (VGS - Vth) * (1 + LAMBDA * VDS)
ro_th = 1.0 / (LAMBDA * A)                 # ro = 1/(λ·Id0), 与 level-1 模型导出一致
Rout_th = float(Rd) * ro_th / (float(Rd) + ro_th)
Av_th_ro = -gm_th * Rout_th
Av_th_noro = -gm_th * float(Rd)
print('【NMOS 共源放大电路】  (模型 KP=1.6m, W/L=1, VTO=1, LAMBDA=0.02)')
print('  手算 V_G = VDD*Rg2/(Rg1+Rg2) = %.4f V' % VG)
print('  手算 V_GS = %.4f V' % VGS)
print('  手算 I_D = %.4f mA' % (ID * 1000))
print('  手算 V_DS = %.4f V' % VDS)
print('  饱和判据: V_DS=%.3f > V_GS-V_th=%.3f => %s'
      % (VDS, VGS - Vth, '饱和区' if VDS > VGS - Vth else '线性区'))
print('  手算 gm = %.4f mA/V  ro = %.1f Ohm  Rout(Rd||ro)=%.1f Ohm'
      % (gm_th * 1000, ro_th, Rout_th))
print('  手算 Av(含ro) = %.4f   Av(不含ro) = %.4f' % (Av_th_ro, Av_th_noro))

# ================= 画 1: 完整放大电路 =================
d = schemdraw.Drawing(show=False)
d.config(unit=2, fontsize=10)
# VDD 顶部横线
d += elm.Line().at((2, 6)).to((8, 6))
d += elm.Label().at((8.3, 6)).label('VDD = 5V')
# Rd (从 VDD 到漏极 d)
d += elm.Resistor().at((4, 6)).to((4, 4)).label('Rd\n2k', loc='right')
# NMOS (漏极在上, 源极在下, 栅极在右)
d += elm.NFet().anchor('drain').at((4, 4))
# 源极 S -> 地
d += elm.Line().at((4, 2.5)).to((4, 1.3))
d += elm.Ground().at((4, 1.3))
# 输出端 v_o (漏极)
d += elm.Dot().at((4, 4))
d += elm.Line().at((4, 4)).to((5.6, 4))
d += elm.Label().at((5.8, 4)).label('v_o')
d += elm.Label().at((3.5, 4.2)).label('d')
# 栅极引线到节点 g
d += elm.Line().at((5.37, 3.25)).to((7.6, 3.25))
d += elm.Dot().at((7.6, 3.25))
d += elm.Label().at((7.8, 3.5)).label('g')
# Rg1 (节点 g 到 VDD)
d += elm.Resistor().at((7.6, 3.25)).to((7.6, 6)).label('Rg1 60k', loc='right')
# Rg2 (节点 g 到地)
d += elm.Resistor().at((7.6, 3.25)).to((7.6, 1.3)).label('Rg2 40k', loc='right')
d += elm.Ground().at((7.6, 1.3))
# Cb1 (耦合电容) + 输入源
d += elm.Capacitor().at((9.2, 3.25)).to((7.6, 3.25)).label('Cb1', loc='top')
d += elm.Line().at((9.2, 3.25)).to((10.8, 3.25))
d += elm.SourceSin().at((10.8, 3.25)).to((10.8, 1.3))
d += elm.Ground().at((10.8, 1.3))
d += elm.Label().at((11.2, 3.25)).label('vi\n10mV')
d.save('figures/mos_full.png')
print('  已保存完整电路图: figures/mos_full.png')

# ================= 画 2: 直流通路 =================
d2 = schemdraw.Drawing(show=False)
d2.config(unit=2, fontsize=10)
d2 += elm.Line().at((2, 6)).to((8, 6))
d2 += elm.Label().at((8.3, 6)).label('VDD = 5V')
d2 += elm.Resistor().at((4, 6)).to((4, 4)).label('Rd\n2k', loc='right')
d2 += elm.NFet().anchor('drain').at((4, 4))
d2 += elm.Line().at((4, 2.5)).to((4, 1.3))
d2 += elm.Ground().at((4, 1.3))
d2 += elm.Dot().at((4, 4))
d2 += elm.Line().at((4, 4)).to((5.6, 4))
d2 += elm.Label().at((5.8, 4)).label('v_o')
d2 += elm.Line().at((5.37, 3.25)).to((7.6, 3.25))
d2 += elm.Dot().at((7.6, 3.25))
d2 += elm.Label().at((7.8, 3.5)).label('g')
d2 += elm.Resistor().at((7.6, 3.25)).to((7.6, 6)).label('Rg1 60k', loc='right')
d2 += elm.Resistor().at((7.6, 3.25)).to((7.6, 1.3)).label('Rg2 40k', loc='right')
d2 += elm.Ground().at((7.6, 1.3))
d2 += elm.Label().at((10, 5.2)).label('(Cb1 open: DC path only)')
d2.save('figures/mos_dc.png')
print('  已保存直流通路图: figures/mos_dc.png')

# ================= 画 3: 小信号等效模型 =================
d3 = schemdraw.Drawing(show=False)
d3.config(unit=2, fontsize=10)
# 输入源 vi (栅极对地) —— 栅极节点 g
d3 += elm.SourceSin().at((0, 2)).to((0, 0)).label('vi', loc='top')
d3 += elm.Ground().at((0, 0))
d3 += elm.Line().at((0, 2)).to((1.2, 2))
d3 += elm.Dot().at((1.2, 2))
d3 += elm.Label().at((1.35, 2.3)).label('g')
# vgs 标注
d3 += elm.Label().at((-0.8, 1.0)).label('vgs')
# 受控电流源 gm*vgs (漏极->地)
d3 += elm.Line().at((1.2, 2)).to((2.6, 2))
d3 += elm.Dot().at((2.6, 2))          # 漏极节点 d
d3 += elm.SourceI().at((2.6, 2)).to((2.6, 0))
d3 += elm.Ground().at((2.6, 0))
d3 += elm.Label().at((3.0, 1.0)).label('gm·vgs')
# 输出支路
d3 += elm.Line().at((2.6, 2)).to((4.2, 2))
d3 += elm.Dot().at((4.2, 2))
d3 += elm.Label().at((4.35, 2.3)).label('v_o')
# Rd (漏极上拉至 AC 地)
d3 += elm.Line().at((4.2, 2)).to((5.6, 2))
d3 += elm.Resistor().at((5.6, 2)).to((5.6, 4)).label('Rd', loc='left')
d3 += elm.Ground().at((5.6, 4))
# ro (漏极到地)
d3 += elm.Resistor().at((4.2, 2)).to((4.2, 0)).label('ro', loc='right')
d3 += elm.Ground().at((4.2, 0))
# 底部地线
d3 += elm.Line().at((0, 0)).to((4.2, 0))
d3.save('figures/mos_small_signal.png')
print('  已保存小信号等效模型图: figures/mos_small_signal.png')

# ================= 直流工作点 =================
c = Circuit('mos_dc')
c.V('vdd', 'vdd', c.gnd, VDD)
c.R('rg1', 'vdd', 'g', Rg1)
c.R('rg2', 'g', c.gnd, Rg2)
c.R('rd', 'vdd', 'd', Rd)
c.model('NMOS', 'nmos', level=1, kp=1.6e-3, vto=1.0, lambda_=0.02)
c.MOSFET('m', 'd', 'g', c.gnd, c.gnd, model='NMOS', w=2, l=2)
sim = c.simulator(temperature=25, nominal_temperature=25)
op = sim.operating_point()
VGS_sim = scalar(op['g'])                 # 源接地 => VGS=Vg
VDS_sim = scalar(op['d'])                 # 源接地 => VDS=Vd
ID_sim = (float(VDD) - VDS_sim) / float(Rd) * 1000   # mA
print('  仿真 V_GS = %.4f V' % VGS_sim)
print('  仿真 I_D = %.4f mA' % ID_sim)
print('  仿真 V_DS = %.4f V' % VDS_sim)

# ================= 小信号 gm, ro (数值偏导) =================
Vds0 = VDS_sim
Vgs0 = VGS_sim

# --- gm: 固定 Vds, 微扰 Vgs ---
def Id_at(Vgs, Vds):
    cg = Circuit('gm')
    cg.V('idmeas', 'd', cg.gnd, Vds @ u_V)   # 固定漏极电压 (电流表)
    cg.V('vg', 'g', cg.gnd, Vgs @ u_V)       # 栅极电压
    cg.model('NMOS', 'nmos', level=1, kp=1.6e-3, vto=1.0, lambda_=0.02)
    cg.MOSFET('m', 'd', 'g', cg.gnd, cg.gnd, model='NMOS', w=2, l=2)
    sg = cg.simulator(temperature=25, nominal_temperature=25)
    og = sg.operating_point()
    return scalar(og.branches['vidmeas'])    # 漏极电流 = Id

dv = 1e-3
Id_hi = Id_at(Vgs0 + dv, Vds0)
Id_lo = Id_at(Vgs0 - dv, Vds0)
gm_sim = abs((Id_hi - Id_lo) / (2 * dv)) * 1000   # mA/V (取幅值)
print('  仿真 gm (数值偏导) = %.4f mA/V' % gm_sim)

# --- ro: 固定 Vgs, 微扰 Vds ---
dd = 5e-3
Id_hi2 = Id_at(Vgs0, Vds0 + dd)
Id_lo2 = Id_at(Vgs0, Vds0 - dd)
ro_sim = abs((2 * dd) / (Id_hi2 - Id_lo2))          # Ohm (取幅值)
print('  仿真 ro (数值偏导) = %.1f Ohm' % ro_sim)

Rout_sim = float(Rd) * ro_sim / (float(Rd) + ro_sim)
Av_small = -gm_sim / 1000 * Rout_sim                # -gm*Rout
print('  仿真 Av(由小信号 gm,ro 计算) = %.4f' % Av_small)

# ================= 瞬时分析 (输入 10mV/1kHz 正弦) =================
ct = Circuit('mos_tran')
ct.V('vdd', 'vdd', ct.gnd, VDD)
ct.R('rg1', 'vdd', 'g', Rg1)
ct.R('rg2', 'g', ct.gnd, Rg2)
ct.R('rd', 'vdd', 'd', Rd)
ct.C('cb1', 'vin', 'g', Cb1)
ct.SinusoidalVoltageSource('in', 'vin', ct.gnd,
                           offset=0 @ u_V, amplitude=Vi_amp @ u_V,
                           frequency=f_in @ u_Hz)
ct.model('NMOS', 'nmos', level=1, kp=1.6e-3, vto=1.0, lambda_=0.02)
ct.MOSFET('m', 'd', 'g', ct.gnd, ct.gnd, model='NMOS', w=2, l=2)
simt = ct.simulator(temperature=25, nominal_temperature=25)
period_s = 1.0 / f_in
tran = simt.transient(step_time=2 @ u_us, end_time=5 * period_s @ u_s)

t = np.asarray(tran.time) * 1000             # ms
vin_t = np.asarray(tran['vin'])
vout_t = np.asarray(tran['d'])

# 取最后一整周期测增益
n = len(t)
tn = np.asarray(tran.time)
# 稳态: 最后两个周期
mask = tn > 3 * period_s
vin_p = np.asarray(tran['vin'])[mask]
vout_p = np.asarray(tran['d'])[mask]
vin_amp_meas = (vin_p.max() - vin_p.min()) / 2
vout_amp_meas = (vout_p.max() - vout_p.min()) / 2
gain_meas = vout_amp_meas / vin_amp_meas
print('  仿真输入幅度 = %.4f mV' % (vin_amp_meas * 1000))
print('  仿真输出幅度 = %.4f mV' % (vout_amp_meas * 1000))
print('  仿真实测增益 |Av| = %.4f  (反相)' % gain_meas)

# 画输入/输出波形 (输出去掉直流偏置, 直观显示反相)
vout_ac = vout_t - np.mean(vout_t[mask])
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(t, vin_t * 1000, 'b-', lw=1.3, label='v_i (mV, 10mV)')
ax.plot(t, vout_ac * 1000, 'r-', lw=1.6, label='v_o (mV, AC-coupled)')
ax.axhline(0, color='k', lw=0.6, ls=':')
ax.set_xlabel('Time (ms)')
ax.set_ylabel('Voltage (mV)')
ax.set_title('NMOS Common-Source Amplifier (inverting): v_i vs v_o (1 kHz)')
ax.grid(True, ls=':')
ax.legend(loc='lower right')
fig.tight_layout()
fig.savefig('figures/mos_transient.png', dpi=130)
plt.close(fig)
print('  已保存输入/输出波形图: figures/mos_transient.png')
print('  输出~输入相位差应为 180° (反相)')

# ================= AC 分析 (1kHz 增益与相位) =================
ca = Circuit('mos_ac')
ca.V('vdd', 'vdd', ca.gnd, VDD)
ca.R('rg1', 'vdd', 'g', Rg1)
ca.R('rg2', 'g', ca.gnd, Rg2)
ca.R('rd', 'vdd', 'd', Rd)
ca.C('cb1', 'vin', 'g', Cb1)
ca.SinusoidalVoltageSource('in', 'vin', ca.gnd,
                           amplitude=Vi_amp @ u_V, frequency=f_in @ u_Hz, offset=0 @ u_V)
ca.model('NMOS', 'nmos', level=1, kp=1.6e-3, vto=1.0, lambda_=0.02)
ca.MOSFET('m', 'd', 'g', ca.gnd, ca.gnd, model='NMOS', w=2, l=2)
sima = ca.simulator(temperature=25, nominal_temperature=25)
ac = sima.ac(start_frequency=10 @ u_Hz, stop_frequency=1 @ u_MHz,
             number_of_points=200, variation='dec')
# 找 1kHz
freq = np.asarray(ac.frequency)
h = np.asarray(ac['d'])
idx1k = int(np.argmin(np.abs(freq - f_in)))
gain_ac = np.abs(h[idx1k])
phase_ac = np.degrees(np.angle(h[idx1k]))
# 低频增益 (远离截止: 取低频处增益作为中频增益)
idx_low = int(np.argmin(np.abs(freq - 100)))
gain_ac_low = np.abs(h[idx_low])
print('  仿真 AC @1kHz: |Av| = %.4f, 相位 = %.1f deg' % (gain_ac, phase_ac))
print('  仿真 AC @100Hz 增益(中频) = %.4f' % gain_ac_low)

# 画 AC 增益曲线
fig2, ax2 = plt.subplots(figsize=(8, 5))
ax2.semilogx(freq, 20 * np.log10(np.abs(h)), 'b-', lw=1.8)
ax2.set_xlabel('Frequency (Hz)')
ax2.set_ylabel('|Av| (dB)')
ax2.set_title('NMOS Common-Source Gain vs Frequency')
ax2.grid(True, which='both', ls=':')
ax2.axvline(f_in, color='r', ls='--', lw=1.2)
ax2.text(f_in * 1.3, -20, 'f=1kHz', color='r')
fig2.tight_layout()
fig2.savefig('figures/mos_ac.png', dpi=130)
plt.close(fig2)
print('  已保存 AC 增益曲线: figures/mos_ac.png')

# ---------------- 对比表 ----------------
print('\n================ 手算 vs 仿真 对比 ================')
print('  V_GS: 手算 %.4f V | 仿真 %.4f V | 偏差 %.3f%%' % (VGS, VGS_sim, abs(VGS_sim - VGS) / VGS * 100))
print('  I_D : 手算 %.4f mA | 仿真 %.4f mA | 偏差 %.3f%%' % (ID * 1000, ID_sim, abs(ID_sim - ID * 1000) / (ID * 1000) * 100))
print('  V_DS: 手算 %.4f V | 仿真 %.4f V | 偏差 %.3f%%' % (VDS, VDS_sim, abs(VDS_sim - VDS) / VDS * 100))
print('  gm  : 手算 %.4f mA/V | 仿真 %.4f mA/V | 偏差 %.3f%%' % (gm_th * 1000, gm_sim, abs(gm_sim - gm_th * 1000) / (gm_th * 1000) * 100))
print('  ro  : 手算 %.1f Ohm | 仿真 %.1f Ohm | 偏差 %.3f%%' % (ro_th, ro_sim, abs(ro_sim - ro_th) / ro_th * 100))
print('  Av  : 手算(含ro) %.4f | 小信号计算 %.4f | 实测(瞬态) %.4f | AC@1k %.4f'
      % (Av_th_ro, Av_small, gain_meas, gain_ac))

# ---------------- 结果写入 UTF-8 txt ----------------
with open('figures/mos_results.txt', 'w', encoding='utf-8') as fh:
    fh.write('NMOS 共源放大电路 结果\n')
    fh.write('VGS_theory_v=%.4f\n' % VGS)
    fh.write('VGS_sim_v=%.4f\n' % VGS_sim)
    fh.write('ID_theory_mA=%.4f\n' % (ID * 1000))
    fh.write('ID_sim_mA=%.4f\n' % ID_sim)
    fh.write('VDS_theory_v=%.4f\n' % VDS)
    fh.write('VDS_sim_v=%.4f\n' % VDS_sim)
    fh.write('gm_theory_mA_V=%.4f\n' % (gm_th * 1000))
    fh.write('gm_sim_mA_V=%.4f\n' % gm_sim)
    fh.write('ro_theory_ohm=%.1f\n' % ro_th)
    fh.write('ro_sim_ohm=%.1f\n' % ro_sim)
    fh.write('Av_theory_ro=%.4f\n' % Av_th_ro)
    fh.write('Av_small=%.4f\n' % Av_small)
    fh.write('Av_gain_meas=%.4f\n' % gain_meas)
    fh.write('Av_ac=%.4f\n' % gain_ac)
    fh.write('Vout_amp_mV=%.4f\n' % (vout_amp_meas * 1000))
    fh.write('phase_ac_deg=%.1f\n' % phase_ac)
print('  已写入结果文件: figures/mos_results.txt')
