"""Divide o suporte de headphone original em BASE + HASTE, compatíveis com o
suporte_TOPO.stl (topo em 97% com luva de 15 mm).

Requer o modelo original em ../_originais/suporte-headphone/ (não versionado) e:
    pip install manifold3d numpy
Uso: python gerar_partes.py
"""
import re
import struct

import numpy as np
from manifold3d import CrossSection, JoinType, Manifold, Mesh

ORIGINAL = "../_originais/suporte-headphone/Headphone_Stand_1.stl"
ESCALA = 0.97            # mesma escala do topo já impresso
TOPO_BASE = 13.0         # altura da base no original (mm)
CORTE_TOPO = 234.05      # altura em que o topo foi cortado no original
FOLGA = 0.2              # folga por lado no encaixe (igual à luva do topo)
LUVA_TOPO = 15.0         # profundidade do furo do topo
ENCAIXE_BASE = 11.0      # profundidade do encaixe na base
RESSALTO = 8.0           # quanto o colar da base sobe acima do tampo da base
PAREDE_COLAR = 2.4       # parede do colar (igual à luva do topo)
CHANFRO = 0.4            # recuo nas pontas da haste (entrada fácil / pé de elefante)


def ler_stl(caminho):
    d = open(caminho, "rb").read()
    n = struct.unpack("<I", d[80:84])[0]
    if len(d) == 84 + n * 50:
        dt = np.dtype([("n", "<f4", (3,)), ("v", "<f4", (9,)), ("a", "<u2")])
        tri = np.frombuffer(d[84:84 + n * 50], dtype=dt)["v"].astype(np.float64)
    else:
        tri = np.array(re.findall(rb"vertex\s+(\S+)\s+(\S+)\s+(\S+)", d), float)
    v, inv = np.unique(np.round(tri.reshape(-1, 3), 4), axis=0, return_inverse=True)
    return Manifold(Mesh(vert_properties=v.astype(np.float32), tri_verts=inv.reshape(-1, 3).astype(np.uint32)))


def salvar_stl(m, caminho):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    t = np.asarray(mesh.tri_verts)
    with open(caminho, "wb") as f:
        f.write(caminho.encode().ljust(80, b" ")[:80])
        f.write(struct.pack("<I", len(t)))
        for a, b, c in v[t]:
            n = np.cross(b - a, c - a)
            n = n / (np.linalg.norm(n) or 1)
            f.write(struct.pack("<12fH", *n, *a, *b, *c, 0))


def relatorio(nome, m):
    bb = m.bounding_box()
    print(f"{nome}: {bb[3] - bb[0]:.1f} x {bb[4] - bb[1]:.1f} x {bb[5] - bb[2]:.1f} mm, "
          f"volume {m.volume() / 1000:.1f} cm³, genus {m.genus()}, status {m.status()}")


original = ler_stl(ORIGINAL)
perfil = CrossSection(original.slice(100).to_polygons()).scale((ESCALA, ESCALA))

# BASE: tampo original + colar com encaixe para a haste
h_base = TOPO_BASE * ESCALA
base = original.trim_by_plane((0, 0, -1), -TOPO_BASE).scale((ESCALA, ESCALA, ESCALA))
colar = perfil.offset(FOLGA + PAREDE_COLAR, JoinType.Round).extrude(RESSALTO).translate((0, 0, h_base))
fundo_encaixe = h_base + RESSALTO - ENCAIXE_BASE
encaixe = perfil.offset(FOLGA, JoinType.Round).extrude(ENCAIXE_BASE + 1).translate((0, 0, fundo_encaixe))
base = (base + colar) - encaixe

# HASTE: do fundo do encaixe da base até o teto da luva do topo
comprimento = CORTE_TOPO * ESCALA - fundo_encaixe
ponta = perfil.offset(-CHANFRO, JoinType.Round)
haste = (ponta.extrude(1) + perfil.extrude(comprimento - 2).translate((0, 0, 1))
         + ponta.extrude(1).translate((0, 0, comprimento - 1)))

salvar_stl(base, "suporte_BASE.stl")
salvar_stl(haste, "suporte_HASTE.stl")
relatorio("suporte_BASE.stl", base)
relatorio("suporte_HASTE.stl", haste)
print(f"altura montada: {CORTE_TOPO * ESCALA + (248 - CORTE_TOPO) * ESCALA:.1f} mm")
