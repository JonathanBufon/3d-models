"""Gancho de mochila para parafusar na lateral da mesa.

Perfil em "J" visto de lado, extrudado na largura. Gera gancho_mochila.stl.
Requer: pip install manifold3d numpy
Uso: python gancho.py [saida.stl]
"""
import struct
import sys

import numpy as np
from manifold3d import CrossSection, Manifold

# --- Parâmetros (mm) ---
LARGURA = 30          # largura do gancho (vira a altura de impressão)
ESPESSURA = 8         # espessura da placa e do "J"
VAO = 35              # espaço interno entre a mesa e a ponta (onde entra a alça)
ALTURA_PLACA = 75     # quanto a placa sobe acima do centro da curva
ALTURA_PONTA = 25     # quanto a ponta sobe acima do centro da curva
FURO = 4.5            # furo para parafuso de madeira 4 mm
CABECA = 9.0          # diâmetro da cabeça do parafuso (escareado 90°)
FUROS_Y = (60, 88)    # altura dos furos a partir da base do gancho
SEG = 96

r_in = VAO / 2
r_out = r_in + ESPESSURA
cx, cy = ESPESSURA + r_in, r_out  # centro da curva; base do gancho em y=0


def perfil():
    anel = CrossSection.circle(r_out, SEG) - CrossSection.circle(r_in, SEG)
    metade_baixo = CrossSection.square((2 * r_out, r_out)).translate((-r_out, -r_out))
    curva = (anel ^ metade_baixo).translate((cx, cy))
    placa = CrossSection.square((ESPESSURA, ALTURA_PLACA - ESPESSURA / 2)).translate((0, cy))
    topo_placa = CrossSection.circle(ESPESSURA / 2, SEG).translate((ESPESSURA / 2, cy + ALTURA_PLACA - ESPESSURA / 2))
    xp = ESPESSURA + VAO
    ponta = CrossSection.square((ESPESSURA, ALTURA_PONTA - ESPESSURA / 2)).translate((xp, cy))
    topo_ponta = CrossSection.circle(ESPESSURA / 2, SEG).translate((xp + ESPESSURA / 2, cy + ALTURA_PONTA - ESPESSURA / 2))
    return curva + placa + topo_placa + ponta + topo_ponta


def furo_escareado(y):
    # Eixo do furo ao longo de X: atravessa a placa; cabeça embutida na face da frente (x = ESPESSURA).
    prof_cone = (CABECA - FURO) / 2
    furo = Manifold.cylinder(ESPESSURA + 2, FURO / 2, FURO / 2, SEG).translate((0, 0, -1))
    cone = Manifold.cylinder(prof_cone + 0.01, FURO / 2, CABECA / 2, SEG).translate((0, 0, ESPESSURA - prof_cone))
    cabeca = Manifold.cylinder(2, CABECA / 2, CABECA / 2, SEG).translate((0, 0, ESPESSURA))
    # cilindro em Z -> eixo X; centro na largura
    return (furo + cone + cabeca).rotate((0, 90, 0)).translate((0, y, LARGURA / 2))


def gancho():
    corpo = perfil().extrude(LARGURA)
    for y in FUROS_Y:
        corpo -= furo_escareado(y)
    return corpo


def salvar_stl(m, caminho):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    t = np.asarray(mesh.tri_verts)
    with open(caminho, "wb") as f:
        f.write(b"gancho mochila".ljust(80, b" "))
        f.write(struct.pack("<I", len(t)))
        for a, b, c in v[t]:
            n = np.cross(b - a, c - a)
            n = n / (np.linalg.norm(n) or 1)
            f.write(struct.pack("<12fH", *n, *a, *b, *c, 0))
    return len(t)


if __name__ == "__main__":
    saida = sys.argv[1] if len(sys.argv) > 1 else "gancho_mochila.stl"
    g = gancho()
    bb = g.bounding_box()
    print(f"{saida}: {salvar_stl(g, saida)} triângulos, volume {g.volume() / 1000:.1f} cm³, "
          f"caixa {bb[3] - bb[0]:.1f} x {bb[4] - bb[1]:.1f} x {bb[5] - bb[2]:.1f} mm, "
          f"genus {g.genus()}")
