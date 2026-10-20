"""Tampa de privacidade deslizante, em clipe, para a webcam do Dell Inspiron 15 3520.

Perfil em "U" invertido que abraça a borda de cima da tampa do notebook. A aba
de trás, levemente inclinada para dentro, faz pressão na traseira e segura o
clipe sem cola. A aba da frente tem uma janela sobre a câmera e um trilho com
uma lingueta deslizante: com o pino de um lado a câmera fica tampada, do outro
fica livre. Clipe, lingueta e pino saem na mesma impressão, lado a lado, e são
montados depois: a lingueta entra pela ponta aberta do trilho e o pino encaixa
nela pela abertura da frente.

Versão fina (tampa_fina_*): a lingueta fica embutida na própria aba da frente,
presa por um encaixe em "V" nas bordas, e a aba inteira tem FINA_ESP de
espessura, para o notebook fechar com o clipe no lugar.

Gera, para cada espessura em ESPESSURAS_TAMPA, normal/tampa_webcam_<esp>mm.stl
e fina/tampa_fina_<esp>mm.stl; em gabaritos/, um gabarito com fendas para
descobrir a espessura real da tampa e lâminas para medir a fresta com o
notebook fechado.
Requer: pip install manifold3d numpy
Uso: python tampa.py
"""
import struct

import numpy as np
from manifold3d import CrossSection, JoinType, Manifold

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
ESPIGA = (2.0, 3.0)   # espiga do pino (Z x Y), entra justa no furo da lingueta
ESPIGA_FOLGA = 0.05   # folga do furo da espiga; aumente se não entrar
ESPACO_MESA = 4.0     # distância entre as peças na mesa de impressão
# versão fina
FINA_ESP = 1.2        # espessura da aba da frente; tem que caber na fresta com o notebook fechado
FINA_LARGURA = 40
FINA_FOLGA = 0.2      # folga da lingueta nas bordas em "V"
FINA_FOLGA_PONTA = 0.5  # folga nas pontas (maior: a ponta de baixo é impressa sobre o vão)
LAMINAS = (0.6, 0.8, 1.0, 1.2, 1.4, 1.6)
GABARITO = (4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5)
SEG = 48


def perfil(lid, frente_esp=FRENTE_ESP):
    """Perfil em XY: tampa do notebook entre x=0 (tela) e x=lid (traseira), borda em y=0."""
    vao = lid + FOLGA
    # abas sobem até o meio da ponte para as peças se fundirem
    frente = CrossSection.square((frente_esp, FRENTE_ALT - frente_esp / 2 + PONTE_ESP / 2)).translate(
        (-frente_esp, -FRENTE_ALT + frente_esp / 2))
    ponta_frente = CrossSection.circle(frente_esp / 2, SEG).translate((-frente_esp / 2, -FRENTE_ALT + frente_esp / 2))
    ponte = CrossSection.square((frente_esp + vao + TRAS_ESP, PONTE_ESP)).translate((-frente_esp, 0))
    # aba de trás inclinada: na raiz o vão é lid+FOLGA, na ponta é lid+FOLGA-APERTO
    y_ponta = -TRAS_ALT + TRAS_ESP / 2
    tras = CrossSection([[  # sentido anti-horário
        (vao - APERTO, y_ponta), (vao + TRAS_ESP - APERTO, y_ponta),
        (vao + TRAS_ESP, PONTE_ESP / 2), (vao, PONTE_ESP / 2),
    ]])
    ponta_tras = CrossSection.circle(TRAS_ESP / 2, SEG).translate((vao - APERTO + TRAS_ESP / 2, y_ponta))
    # cantos externos da ponte arredondados
    r = PONTE_ESP / 2
    x0, x1 = -frente_esp, vao + TRAS_ESP
    corpo = frente + ponta_frente + ponte + tras + ponta_tras
    for x, sx in ((x0, 1), (x1, -1)):
        canto = CrossSection.square((r, r)).translate((x if sx > 0 else x - r, PONTE_ESP - r))
        arredondado = CrossSection.circle(r, SEG).translate((x + sx * r, PONTE_ESP - r))
        corpo = corpo - (canto - arredondado)
    return corpo


def caixa(x0, x1, y0, y1, z0, z1):
    return Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))


def clipe(lid):
    """Clipe, lingueta e pino na posição montada, com a lingueta fechada.

    Coordenadas da peça deitada de lado (Z = largura). O trilho é aberto em z=0,
    por onde a lingueta entra; ali os lábios se unem numa barra (z < BARRA) que
    barra o pino. Do outro lado, a parede FIM_ESP limita a abertura.
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

    barra = 2.0
    corpo = perfil(lid).extrude(LARGURA)
    corpo += caixa(x_frente, -FRENTE_ESP + 0.01, -FRENTE_ALT, PONTE_ESP, 0, LARGURA)
    corpo -= caixa(x_trilho, -FRENTE_ESP, y_cav0, 0, -1, z_fim)                     # cavidade da lingueta
    corpo -= caixa(x_frente - 1, x_trilho + 0.01, abertura_y[0], abertura_y[1], barra, z_fim)
    corpo -= caixa(-FRENTE_ESP - 1, 0.01, *jan_y, zc - jw / 2, zc + jw / 2)          # janela na aba da frente

    # lingueta na posição fechada: o furo dela fica CURSO abaixo da janela
    furo_z = zc - jw / 2 - CURSO
    assert furo_z + jw + 2 <= zc - jw / 2 and LING_COMP + CURSO + g <= z_fim, "curso ou comprimento incompatível"
    pz = barra + g
    ez, ey = ESPIGA
    ec = ((abertura_y[0] + abertura_y[1]) / 2, pz + PINO[0] / 2)                    # centro da espiga (y, z)
    espiga_furo = lambda folga, x0, x1: caixa(x0, x1, ec[0] - ey / 2 - folga, ec[0] + ey / 2 + folga,
                                              ec[1] - ez / 2 - folga, ec[1] + ez / 2 + folga)
    ling = caixa(x_trilho + g, -FRENTE_ESP - g, *ling_y, 0, LING_COMP)
    ling -= caixa(x_trilho, -FRENTE_ESP, *jan_y, furo_z, furo_z + jw)
    ling -= espiga_furo(ESPIGA_FOLGA, x_trilho, -FRENTE_ESP)
    # pino: cabeça entre os lábios + espiga que não chega à face de trás da lingueta
    pino = caixa(x_frente - PINO[1], x_trilho + g, abertura_y[0] + g, abertura_y[1] - g, pz, pz + PINO[0])
    pino += espiga_furo(0, x_trilho + g - 0.01, -FRENTE_ESP - g - 0.15)
    return corpo, ling, pino


def mesa_normal(lid):
    """As três peças lado a lado para uma impressão só, cada uma na melhor posição.

    Clipe deitado de lado (perfil em "U" na mesa); lingueta deitada; pino com a
    cabeça na mesa e a espiga para cima.
    """
    corpo, ling, pino = clipe(lid)
    ling = ling.rotate((0, -90, 0))      # face da frente (menor X) vai para a mesa
    pino = pino.rotate((0, -90, 0))
    pecas, x = Manifold(), None
    for p in (corpo, ling, pino):
        bb = p.bounding_box()
        x = bb[0] if x is None else x
        pecas += p.translate((x - bb[0], -bb[1], -bb[2]))
        x += bb[3] - bb[0] + ESPACO_MESA
    return pecas


def pontudo(z0, z1, y0, y1):
    """Prisma ao longo de X com contorno de frente (Z, Y) em hexágono alongado: pontas a 45° em z0 e z1."""
    ym, hh = (y0 + y1) / 2, (y1 - y0) / 2
    return CrossSection([[(z0, ym), (z0 + hh, y0), (z1 - hh, y0), (z1, ym), (z1 - hh, y1), (z0 + hh, y1)]])


def em_x(contorno_zy, x0, x1):
    """Extruda um contorno desenhado em (Z, Y) ao longo de X, de x0 a x1."""
    return contorno_zy.extrude(x1 - x0).rotate((0, -90, 0)).translate((x1, 0, 0))


def clipe_fino(lid):
    """Clipe com a lingueta embutida na aba da frente, impresso deitado de lado (Z para cima).

    Corte (X, Y): a fenda tem bordas em "V" que entram na aba, e a lingueta tem as
    bordas em "V" correspondentes; assim ela não sai nem para a frente nem para trás.
    Vista de frente (Z, Y): fenda e lingueta têm pontas a 45°, que imprimem sem suporte
    e servem de batente nas duas pontas do curso.
    """
    t, g = FINA_ESP, FINA_FOLGA
    v = t / 2                                   # profundidade do "V", a 45°
    jw, jh = JANELA
    jan_y = (JANELA_Y - jh / 2, JANELA_Y + jh / 2)
    s0, s1 = jan_y[0] - v, jan_y[1] + v         # fenda no meio da espessura; nas faces fica igual à janela
    hh = (s1 - s0) / 2
    zc = FINA_LARGURA / 2
    # lingueta: fechada cobre a janela com sobra de 0,3 mm; aberta, a ponta passa da janela
    ling0 = zc - jw / 2 - hh - 0.3
    ling1 = zc + jw / 2 + hh + 0.3
    curso = (zc + jw / 2 + 0.2) - ling0
    gp = FINA_FOLGA_PONTA * 2 ** 0.5            # folga na ponta medida ao longo de Z
    fenda = (ling0 - gp, ling1 + curso + gp)
    assert s1 < -0.5 and s0 > -FRENTE_ALT + 1.5 and fenda[0] > 2 and fenda[1] < FINA_LARGURA - 2

    perfil_v = CrossSection([[
        (-t - 1, s0 + v), (-t, s0 + v), (-t / 2, s0), (0, s0 + v), (1, s0 + v),
        (1, s1 - v), (0, s1 - v), (-t / 2, s1), (-t, s1 - v), (-t - 1, s1 - v),
    ]])
    fenda_3d = perfil_v.extrude(FINA_LARGURA + 2).translate((0, 0, -1)) ^ em_x(pontudo(*fenda, s0, s1), -t - 1, 1)
    corpo = perfil(lid, t).extrude(FINA_LARGURA) - fenda_3d

    hexa = CrossSection([[(-t, s0 + v), (-t / 2, s0), (0, s0 + v), (0, s1 - v), (-t / 2, s1), (-t, s1 - v)]])
    ling = hexa.offset(-g, JoinType.Miter).extrude(FINA_LARGURA) ^ \
        em_x(pontudo(ling0, ling1, s0, s1).offset(-0.01, JoinType.Miter), -t - 1, 1)
    # ranhuras na face da frente para o dedo não escorregar
    for k in range(-2, 3):
        z = (ling0 + ling1) / 2 + k * 1.6
        ling -= caixa(-t - 1, -t + g + 0.2, s0, s1, z - 0.3, z + 0.3)
    return corpo + ling, curso


def laminas():
    """Lâminas de espessura para medir a fresta entre a moldura e o teclado com o notebook fechado."""
    pecas = Manifold()
    for i, e in enumerate(LAMINAS):
        lam = Manifold.cube((10, 30, e))
        # entalhes na ponta de trás: 1 entalhe = 0,6 mm, cada entalhe a mais soma 0,2 mm
        for k in range(i + 1):
            lam -= Manifold.cube((0.8, 1.5, e + 2)).translate((1 + k * 1.4, 28.5, -1))
        pecas += lam.translate((i * 13, 0, 0))
    return pecas


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
    import os

    for pasta in ("normal", "fina", "gabaritos"):
        os.makedirs(pasta, exist_ok=True)
    for lid in ESPESSURAS_TAMPA:
        nome = f"{lid:.1f}mm.stl".replace(".", "_", 1)
        relatorio(mesa_normal(lid), f"normal/tampa_webcam_{nome}", "tampa webcam")
        fino, curso = clipe_fino(lid)
        relatorio(fino, f"fina/tampa_fina_{nome}", "tampa webcam fina")
    print(f"curso da lingueta fina: {curso:.1f} mm")
    relatorio(gabarito(), "gabaritos/gabarito_espessura.stl", "gabarito espessura")
    relatorio(laminas(), "gabaritos/laminas_fresta.stl", "laminas fresta")
