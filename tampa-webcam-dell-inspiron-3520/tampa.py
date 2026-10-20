"""Tampa de privacidade deslizante, em clipe, para a webcam do Dell Inspiron 15 3520.

Perfil em "U" invertido que abraça a borda de cima da tampa do notebook. A aba
de trás, levemente inclinada para dentro, faz pressão na traseira e segura o
clipe sem cola. A aba da frente tem uma janela sobre a câmera e um trilho com
uma lingueta deslizante: com o pino de um lado a câmera fica tampada, do outro
fica livre. A lingueta é impressa já dentro do trilho (print-in-place).
Gera tampa_webcam_<espessura>mm.stl para cada espessura em ESPESSURAS_TAMPA
e um gabarito com fendas para descobrir a espessura real da tampa.
Requer: pip install manifold3d numpy
Uso: python tampa.py
"""
import struct

import numpy as np
from manifold3d import CrossSection, Manifold

# --- Parâmetros (mm) ---
ESPESSURAS_TAMPA = (5.0, 5.5, 6.0, 6.5, 7.0)  # espessura da tampa (tela fechada não conta)
LARGURA = 40          # largura do clipe (janela centrada na câmera)
FRENTE_ESP = 1.0      # aba da frente, encostada na moldura
FRENTE_ALT = 9.5      # quanto a aba da frente desce a partir da borda (não pode passar da moldura)
PONTE_ESP = 1.6       # parte de cima, apoiada na borda da tampa
TRAS_ESP = 1.8        # aba de trás
TRAS_ALT = 16         # quanto a aba de trás desce
FOLGA = 0.2           # folga junto da borda, para entrar sem forçar
APERTO = 0.8          # quanto a ponta da aba de trás avança para dentro (pressão)
# trilho e lingueta
LING_ESP = 1.0        # espessura da lingueta
LABIO_ESP = 0.8       # lábios da frente que seguram a lingueta no trilho
LABIO_COBRE = 1.0     # quanto cada lábio cobre a borda da lingueta
FUNDO_ESP = 1.0       # parede de baixo do trilho
FIM_ESP = 3.7         # parede que fecha o trilho na ponta de cima da impressão
FOLGA_LING = 0.3      # folga da lingueta em todos os lados (print-in-place)
JANELA = (6.0, 5.0)   # largura x altura da janela da câmera
JANELA_Y = -4.0       # centro da janela abaixo da borda da tampa
CURSO = 9.0           # deslocamento da lingueta entre fechada e aberta
LING_COMP = 27.0      # comprimento da lingueta
PINO = (4.0, 0.6)     # largura do pino de puxar e quanto passa dos lábios
GABARITO = (4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5)
SEG = 48


def perfil(lid):
    """Perfil em XY: tampa do notebook entre x=0 (tela) e x=lid (traseira), borda em y=0."""
    vao = lid + FOLGA
    # abas sobem até o meio da ponte para as peças se fundirem
    frente = CrossSection.square((FRENTE_ESP, FRENTE_ALT - FRENTE_ESP / 2 + PONTE_ESP / 2)).translate(
        (-FRENTE_ESP, -FRENTE_ALT + FRENTE_ESP / 2))
    ponta_frente = CrossSection.circle(FRENTE_ESP / 2, SEG).translate((-FRENTE_ESP / 2, -FRENTE_ALT + FRENTE_ESP / 2))
    ponte = CrossSection.square((FRENTE_ESP + vao + TRAS_ESP, PONTE_ESP)).translate((-FRENTE_ESP, 0))
    # aba de trás inclinada: na raiz o vão é lid+FOLGA, na ponta é lid+FOLGA-APERTO
    y_ponta = -TRAS_ALT + TRAS_ESP / 2
    tras = CrossSection([[  # sentido anti-horário
        (vao - APERTO, y_ponta), (vao + TRAS_ESP - APERTO, y_ponta),
        (vao + TRAS_ESP, PONTE_ESP / 2), (vao, PONTE_ESP / 2),
    ]])
    ponta_tras = CrossSection.circle(TRAS_ESP / 2, SEG).translate((vao - APERTO + TRAS_ESP / 2, y_ponta))
    # cantos externos da ponte arredondados
    r = PONTE_ESP / 2
    x0, x1 = -FRENTE_ESP, vao + TRAS_ESP
    corpo = frente + ponta_frente + ponte + tras + ponta_tras
    for x, sx in ((x0, 1), (x1, -1)):
        canto = CrossSection.square((r, r)).translate((x if sx > 0 else x - r, PONTE_ESP - r))
        arredondado = CrossSection.circle(r, SEG).translate((x + sx * r, PONTE_ESP - r))
        corpo = corpo - (canto - arredondado)
    return corpo


def caixa(x0, x1, y0, y1, z0, z1):
    return Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))


def clipe(lid):
    """Clipe com trilho e lingueta, impresso deitado de lado (Z = largura, para cima).

    A lingueta sai da mesa (z=0) na posição fechada. O lado z=0 do trilho é aberto
    e quem segura a lingueta ali é o dente do lábio de cima, que trava o pino;
    o lado de cima é fechado pela parede FIM_ESP, que limita a abertura.
    """
    g = FOLGA_LING
    x_trilho = -FRENTE_ESP - 2 * g - LING_ESP          # fundo do trilho (face da frente da cavidade)
    x_frente = x_trilho - LABIO_ESP                     # face da frente dos lábios
    y_cav0 = -FRENTE_ALT + FUNDO_ESP                    # chão da cavidade
    ling_y = (y_cav0 + g, -g)
    abertura_y = (ling_y[0] + LABIO_COBRE, ling_y[1] - LABIO_COBRE)
    z_fim = LARGURA - FIM_ESP
    zc = LARGURA / 2
    jw, jh = JANELA
    jan_y = (JANELA_Y - jh / 2, JANELA_Y + jh / 2)
    assert abertura_y[0] < jan_y[0] and jan_y[1] < abertura_y[1], "janela fora da abertura entre os lábios"

    corpo = perfil(lid).extrude(LARGURA)
    corpo += caixa(x_frente, -FRENTE_ESP + 0.01, -FRENTE_ALT, PONTE_ESP, 0, LARGURA)
    corpo -= caixa(x_trilho, -FRENTE_ESP, y_cav0, 0, -1, z_fim)                     # cavidade da lingueta
    dente = 2.0                                                                       # dente no lábio de cima, em z<dente
    corpo -= caixa(x_frente - 1, x_trilho + 0.01, abertura_y[0], abertura_y[1], dente, z_fim)
    corpo -= caixa(x_frente - 1, x_trilho + 0.01, abertura_y[0], abertura_y[1] - 1.5, -1, dente + 0.01)
    corpo -= caixa(-FRENTE_ESP - 1, 0.01, *jan_y, zc - jw / 2, zc + jw / 2)          # janela na aba da frente

    # lingueta na posição fechada: o furo dela fica CURSO abaixo da janela
    furo_z = zc - jw / 2 - CURSO
    assert furo_z + jw + 2 <= zc - jw / 2 and LING_COMP + CURSO + g <= z_fim, "curso ou comprimento incompatível"
    ling = caixa(x_trilho + g, -FRENTE_ESP - g, *ling_y, 0, LING_COMP)
    ling -= caixa(x_trilho, -FRENTE_ESP, *jan_y, furo_z, furo_z + jw)
    pz = dente + g
    ling += caixa(x_frente - PINO[1], x_trilho + g + 0.01, abertura_y[0] + g, abertura_y[1] - g, pz, pz + PINO[0])
    return corpo + ling


def gabarito():
    """Régua com fendas: a que entrar justa na borda da tampa indica qual STL imprimir."""
    passo, prof, alt, esp = 11.0, 8.0, 12.0, 3.0
    comp = passo * len(GABARITO) + 4
    corpo = Manifold.cube((comp, alt, esp))
    for i, e in enumerate(GABARITO):
        x = 4 + i * passo + (passo - 4 - e) / 2
        corpo -= Manifold.cube((e, prof + 1, esp + 2)).translate((x, alt - prof, -1))
        # marcas rebaixadas sob cada fenda: 1 marca = 4,5 mm, cada marca a mais soma 0,5 mm
        for k in range(round((e - GABARITO[0]) / 0.5) + 1):
            corpo -= Manifold.cube((0.8, 0.8, 0.6)).translate((4 + i * passo + k * 1.2 - 0.6, 1.2, esp - 0.6))
    return corpo


def salvar_stl(m, caminho, nome):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    t = np.asarray(mesh.tri_verts)
    with open(caminho, "wb") as f:
        f.write(nome.encode().ljust(80, b" "))
        f.write(struct.pack("<I", len(t)))
        for a, b, c in v[t]:
            n = np.cross(b - a, c - a)
            n = n / (np.linalg.norm(n) or 1)
            f.write(struct.pack("<12fH", *n, *a, *b, *c, 0))
    return len(t)


def relatorio(m, caminho, nome):
    bb = m.bounding_box()
    print(f"{caminho}: {salvar_stl(m, caminho, nome)} triângulos, volume {m.volume() / 1000:.2f} cm³, "
          f"caixa {bb[3] - bb[0]:.1f} x {bb[4] - bb[1]:.1f} x {bb[5] - bb[2]:.1f} mm, genus {m.genus()}")


if __name__ == "__main__":
    for lid in ESPESSURAS_TAMPA:
        relatorio(clipe(lid), f"tampa_webcam_{lid:.1f}mm.stl".replace(".", "_", 1), "tampa webcam")
    relatorio(gabarito(), "gabarito_espessura.stl", "gabarito espessura")
